# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import os

from kubernetes import client as k8s_config
from kubernetes.client import api_client
from kubernetes.client.apis import core_v1_api
from kubernetes.client.apis import apps_v1_api
from kubernetes.client.apis import extensions_v1beta1_api
from kubernetes.client.apis import version_api
from kubernetes.client import rest
from kubernetes.client.apis import storage_v1_api
from kubernetes.stream import stream
from rally.common import cfg
from rally.common import logging
from rally.common import utils as commonutils
from rally import exceptions
from rally.task import atomic
from rally.task import service

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


def wait_for_status(name, status, read_method, resource_type=None, **kwargs):
    """Util method for polling status until it won't be equals to `status`.

    :param name: resource name
    :param status: status waiting for
    :param read_method: method to poll
    :param resource_type: resource type for extended exceptions
    :param kwargs: additional kwargs for read_method
    """
    sleep_time = CONF.kubernetes.status_poll_interval
    retries_total = CONF.kubernetes.status_total_retries

    LOG.info("%s retries" % retries_total)

    commonutils.interruptable_sleep(CONF.kubernetes.start_prepoll_delay)

    i = 0
    while i < retries_total:
        resp = read_method(name=name, **kwargs)
        resp_id = resp.metadata.uid
        current_status = resp.status.phase
        if resp.status.phase != status:
            i += 1
            commonutils.interruptable_sleep(sleep_time)
        else:
            return
        if i == retries_total:
            raise exceptions.TimeoutException(
                desired_status=status,
                resource_name=name,
                resource_type=resource_type,
                resource_id=resp_id or "<no id>",
                resource_status=current_status,
                timeout=(retries_total * sleep_time))


def wait_for_ready_replicas(name, read_method, resource_type=None,
                            replicas=None, **kwargs):
    """Util method for polling status until it won't be equals to `status`.

    :param name: resource name
    :param read_method: method to poll
    :param resource_type: resource type for extended exceptions
    :param replicas: replicaset expected replicas for extended exceptions
    :param kwargs: additional kwargs for read_method
    """
    sleep_time = CONF.kubernetes.status_poll_interval
    retries_total = CONF.kubernetes.status_total_retries

    commonutils.interruptable_sleep(CONF.kubernetes.start_prepoll_delay)

    i = 0
    while i < retries_total:
        resp = read_method(name=name, **kwargs)
        resp_id = resp.metadata.uid
        current_status = resp.status.replicas
        ready_replicas = resp.status.ready_replicas
        if (current_status is None or
                ready_replicas is None or
                current_status != ready_replicas):
            i += 1
            commonutils.interruptable_sleep(sleep_time)
        else:
            return
        if i == retries_total:
            raise exceptions.TimeoutException(
                desired_status=replicas,
                resource_name=name,
                resource_type=resource_type,
                resource_id=resp_id or "<no id>",
                resource_status=current_status,
                timeout=(retries_total * sleep_time))


def wait_for_not_found(name, read_method, resource_type=None, **kwargs):
    """Util method for polling status while resource exists.

    :param name: resource name
    :param read_method: method to poll
    :param resource_type: resource type for extended exceptions
    :param kwargs: additional kwargs for read_method
    """
    sleep_time = CONF.kubernetes.status_poll_interval
    retries_total = CONF.kubernetes.status_total_retries

    commonutils.interruptable_sleep(CONF.kubernetes.start_prepoll_delay)

    i = 0
    while i < retries_total:
        try:
            resp = read_method(name=name, **kwargs)
            resp_id = resp.metadata.uid
            if kwargs.get("replicas"):
                current_status = "%s replicas" % resp.status.replicas
            else:
                current_status = resp.status.phase
        except rest.ApiException as ex:
            if ex.status == 404:
                return
            else:
                raise
        else:
            commonutils.interruptable_sleep(sleep_time)
            i += 1
        if i == retries_total:
            raise exceptions.TimeoutException(
                desired_status="Terminated",
                resource_name=name,
                resource_type=resource_type,
                resource_id=resp_id or "<no id>",
                resource_status=current_status,
                timeout=(retries_total * sleep_time))


class Kubernetes(service.Service):
    """A wrapper for python kubernetes client.

    This class handles different ways for initialization of kubernetesclient.
    """

    def __init__(self, spec, name_generator=None, atomic_inst=None):
        super(Kubernetes, self).__init__(None,
                                         name_generator=name_generator,
                                         atomic_inst=atomic_inst)
        self._spec = spec

        # NOTE(andreykurilin): KubernetesClient doesn't provide any __version__
        #   property to identify the client version (you are welcome to fix
        #   this code if I'm wrong). Let's check for some backward incompatible
        #   changes to identify the way to communicate with it.
        if hasattr(k8s_config, "ConfigurationObject"):
            # Actually, it is `k8sclient < 4.0.0`, so it can be
            #   kubernetesclient 2.0 or even less, but it doesn't make any
            #   difference for us
            self._k8s_client_version = 3
        else:
            self._k8s_client_version = 4

        if self._k8s_client_version == 3:
            config = k8s_config.ConfigurationObject()
        else:
            config = k8s_config.Configuration()

        config.host = self._spec["server"]
        config.ssl_ca_cert = self._spec["certificate-authority"]
        if self._spec.get("api_key"):
            config.api_key = {"authorization": self._spec["api_key"]}
            if self._spec.get("api_key_prefix"):
                config.api_key_prefix = {
                    "authorization": self._spec["api_key_prefix"]}
        else:
            config.cert_file = self._spec["client-certificate"]
            config.key_file = self._spec["client-key"]
            if self._spec.get("tls_insecure", False):
                config.verify_ssl = False

        if self._k8s_client_version == 3:
            api = api_client.ApiClient(config=config)
        else:
            api = api_client.ApiClient(configuration=config)

        self.api = api
        self.v1_client = core_v1_api.CoreV1Api(api)
        self.v1_storage = storage_v1_api.StorageV1Api(api)
        self.v1beta1_ext = extensions_v1beta1_api.ExtensionsV1beta1Api(api)
        self.v1_apps = apps_v1_api.AppsV1Api(api)

    def get_version(self):
        return version_api.VersionApi(self.api).get_code().to_dict()

    @classmethod
    def create_spec_from_file(cls):
        from kubernetes.config import kube_config

        cfg_file = kube_config.KUBE_CONFIG_DEFAULT_LOCATION
        if not os.path.exists(os.path.expanduser(cfg_file)):
            return {}

        kube_config.load_kube_config()
        k8s_cfg = k8s_config.Configuration()
        return {
            "host": k8s_cfg.host,
            "certificate-authority": k8s_cfg.ssl_ca_cert,
            "api_key": k8s_cfg.api_key,
            "api_key_prefix": k8s_cfg.api_key_prefix,
            "client-certificate": k8s_cfg.cert_file,
            "client-key": k8s_cfg.key_file,
            "tls_insecure": k8s_cfg.verify_ssl
        }

    @atomic.action_timer("kubernetes.list_namespaces")
    def list_namespaces(self):
        """List namespaces."""
        return [{"name": r.metadata.name,
                 "uid": r.metadata.uid,
                 "labels": r.metadata.labels}
                for r in self.v1_client.list_namespace().items]

    @atomic.action_timer("kubernetes.get_namespace")
    def get_namespace(self, name):
        """Get namespace status.

        :param name: namespace name
        """
        return self.v1_client.read_namespace(name)

    @atomic.action_timer("kubernetes.create_namespace")
    def create_namespace(self, name, status_wait=True):
        """Create namespace and wait until status phase won't be Active.

        :param name: namespace name
        :param status_wait: wait namespace for Active status
        """
        name = name or self.generate_random_name()

        manifest = {
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {
                "name": name,
                "labels": {
                    "role": name
                }
            }
        }
        self.v1_client.create_namespace(body=manifest)

        if status_wait:
            with atomic.ActionTimer(self,
                                    "kubernetes.wait_for_nc_become_active"):
                wait_for_status(name,
                                status="Active",
                                read_method=self.get_namespace)
        return name

    @atomic.action_timer("kubernetes.delete_namespace")
    def delete_namespace(self, name, status_wait=True):
        """Delete namespace and wait it's full termination.

        :param name: namespace name
        :param status_wait: wait namespace for termination
        """
        self.v1_client.delete_namespace(name=name,
                                        body=k8s_config.V1DeleteOptions())

        if status_wait:
            with atomic.ActionTimer(self,
                                    "kubernetes.wait_namespace_termination"):
                wait_for_not_found(name,
                                   read_method=self.get_namespace)

    @atomic.action_timer("kubernetes.create_serviceaccount")
    def create_serviceaccount(self, name, namespace):
        """Create serviceAccount for namespace.

        :param name: serviceAccount name
        :param namespace: namespace where sa should be created
        """
        sa_manifest = {
            "apiVersion": "v1",
            "kind": "ServiceAccount",
            "metadata": {
                "name": name
            }
        }
        self.v1_client.create_namespaced_service_account(namespace=namespace,
                                                         body=sa_manifest)

    @atomic.action_timer("kubernetes.create_secret")
    def create_secret(self, name, namespace):
        """Create secret with token for namespace.

        :param name: secret name
        :param namespace: namespace where secret should be created
        """
        secret_manifest = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {
                "name": name,
                "annotations": {
                    "kubernetes.io/service-account.name": name
                }
            }
        }
        self.v1_client.create_namespaced_secret(namespace=namespace,
                                                body=secret_manifest)

    @atomic.action_timer("kubernetes.get_pod")
    def get_pod(self, name, namespace):
        """Get pod status.

        :param name: pod's name
        :param namespace: pod's namespace
        """
        return self.v1_client.read_namespaced_pod(name, namespace=namespace)

    @atomic.action_timer("kubernetes.create_pod")
    def create_pod(self, name, image, namespace, command=None,
                   status_wait=True):
        """Create pod and wait until status phase won't be Running.

        :param name: pod's custom name
        :param image: pod's image
        :param namespace: chosen namespace to create pod into
        :param command: array of strings which represents container command
        :param status_wait: wait pod for Running status
        """
        name = name or self.generate_random_name()

        container_spec = {
            "name": name,
            "image": image
        }
        if command is not None and isinstance(command, (list, tuple)):
            container_spec["command"] = list(command)

        manifest = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {
                "name": name,
                "labels": {
                    "role": self._spec.get("env_id") or name
                }
            },
            "spec": {
                "serviceAccountName": namespace,
                "containers": [container_spec]
            }
        }

        if not self._spec.get("serviceaccounts"):
            del manifest["spec"]["serviceAccountName"]

        self.v1_client.create_namespaced_pod(body=manifest,
                                             namespace=namespace)

        if status_wait:
            with atomic.ActionTimer(self,
                                    "kubernetes.wait_for_pod_become_running"):
                wait_for_status(name,
                                status="Running",
                                read_method=self.get_pod,
                                namespace=namespace)
        return name

    @atomic.action_timer("kubernetes.delete_pod")
    def delete_pod(self, name, namespace, status_wait=True):
        """Delete pod and wait it's full termination.

        :param name: pod's name
        :param namespace: pod's namespace
        :param status_wait: wait pod for termination
        """
        self.v1_client.delete_namespaced_pod(
            name,
            namespace=namespace,
            body=k8s_config.V1DeleteOptions()
        )

        if status_wait:
            with atomic.ActionTimer(self,
                                    "kubernetes.wait_pod_termination"):
                wait_for_not_found(name,
                                   read_method=self.get_pod,
                                   namespace=namespace)

    @atomic.action_timer("kube.create_replication_controller")
    def create_rc(self, name, replicas, image, namespace, sleep_time=5,
                  retries_total=30, command=None):
        """Create RC and wait until it won't be running.

        :param name: replication controller name
        :param replicas: number of replicas
        :param image: image for each replica
        :param namespace: replication controller namespace
        :param sleep_time: sleep time between each two retries
        :param retries_total: total number of retries
        :param command: array of strings representing container command
        :return: True if create finished successfully and False otherwise
        """

        app = self.generate_random_name()

        container_spec = {
            "name": name,
            "image": image
        }
        if command is not None and isinstance(command, (list, tuple)):
            container_spec["command"] = list(command)

        manifest = {
            "apiVersion": "v1",
            "kind": "ReplicationController",
            "metadata": {
                "name": name,
            },
            "spec": {
                "replicas": replicas,
                "selector": {
                    "app": app
                },
                "template": {
                    "metadata": {
                        "name": name,
                        "labels": {
                            "app": app
                        }
                    },
                    "spec": {
                        "serviceAccountName": namespace,
                        "containers": [container_spec]
                    }
                }
            }
        }

        if not self._spec.get("serviceaccounts"):
            del manifest["spec"]["template"]["spec"]["serviceAccountName"]

        i = 0
        create_started = False
        while i < retries_total:
            LOG.debug("Attempt number %s" % i)
            try:
                self.v1_client.create_namespaced_replication_controller(
                    body=manifest, namespace=namespace)
                LOG.info("RC %s created" % name)
            except Exception as ex:
                LOG.error("RC create failed: %s" % ex.message)
                i += 1
                commonutils.interruptable_sleep(sleep_time)
            else:
                create_started = True
                break

        if not create_started:
            return False

        i = 0
        LOG.debug("Wait until RC pods won't be ready")
        while i < retries_total:
            LOG.debug("Attempt number %s" % i)
            try:
                resp = self.v1_client.read_namespaced_replication_controller(
                    name=name, namespace=namespace)
            except Exception as ex:
                LOG.warning("Unable to read RC status: %s" % ex.message)
                i += 1
                commonutils.interruptable_sleep(sleep_time)
            else:
                if resp.status.ready_replicas != resp.status.replicas:
                    i += 1
                    commonutils.interruptable_sleep(sleep_time)
                else:
                    return True
        return False

    def get_rc_replicas(self, name, namespace):
        """Util method for get RC's current number of replicas."""
        resp = self.v1_client.read_namespaced_replication_controller(
            name=name, namespace=namespace)
        return resp.spec.replicas

    @atomic.action_timer("kube.scale_replication_controller")
    def scale_rc(self, name, namespace, replicas, sleep_time=5,
                 retries_total=30):
        """Scale RC with number of replicas.

        :param name: RC name
        :param namespace: RC namespace
        :param replicas: number of replicas RC scale to
        :param sleep_time: sleep time between each two retries
        :param retries_total: total number of retries
        :returns True if scale successful and False otherwise
        """
        self.v1_client.patch_namespaced_replication_controller(
            name=name,
            namespace=namespace,
            body={"spec": {"replicas": replicas}}
        )
        i = 0
        LOG.debug("Wait until RC pods won't be ready")
        while i < retries_total:
            LOG.debug("Attempt number %s" % i)
            try:
                resp = self.v1_client.read_namespaced_replication_controller(
                    name=name, namespace=namespace)
            except Exception as ex:
                LOG.warning("Unable to read RC status: %s" % ex.message)
                i += 1
                commonutils.interruptable_sleep(sleep_time)
            else:
                if resp.status.ready_replicas != resp.status.replicas:
                    i += 1
                    commonutils.interruptable_sleep(sleep_time)
                else:
                    return True
        return False

    @atomic.action_timer("kube.delete_replication_controller")
    def delete_rc(self, name, namespace, sleep_time=5, retries_total=30):
        """Delete RC from namespace and wait until it won't be terminated.

        :param name: replication controller name
        :param namespace: namespace name of defined RC
        :param sleep_time: sleep time between each two retries
        :param retries_total: total number of retries
        :returns True if delete successful and False otherwise
        """
        resp = self.v1_client.delete_namespaced_replication_controller(
            name=name, namespace=namespace, body=k8s_config.V1DeleteOptions())
        LOG.info("RC %(name)s delete started. Status: %(status)s" % {
            "name": name,
            "status": resp.status
        })

        i = 0
        while i < retries_total:
            LOG.debug("Attempt number %s" % i)
            try:
                self.v1_client.read_namespaced_replication_controller_status(
                    name=name, namespace=namespace)
            except Exception:
                return True
            else:
                commonutils.interruptable_sleep(sleep_time)
                i += 1
        return False

    @atomic.action_timer("kube.create_emptydir_volume_pod")
    def create_emptydir_volume_pod(self, name, image, mount_path, namespace,
                                   command=None):
        """Create pod with emptyDir volume.

        :param name: pod's name
        :param image: pod's image
        :param mount_path: pod's mount path of volume
        :param namespace: pod's namespace
        :param command: array of strings representing container command
        """
        container_spec = {
            "name": name,
            "image": image,
            "volumeMounts": [
                {
                    "mountPath": mount_path,
                    "name": "%s-volume" % name
                }
            ]
        }
        if command is not None and isinstance(command, (list, tuple)):
            container_spec["command"] = list(command)

        manifest = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {
                "name": name,
                "labels": {
                    "role": "rally-test"
                }
            },
            "spec": {
                "serviceAccountName": namespace,
                "containers": [container_spec],
                "volumes": [
                    {
                        "name": "%s-volume" % name,
                        "emptyDir": {}
                    }
                ]
            }
        }

        if not self._spec.get("serviceaccounts"):
            del manifest["spec"]["serviceAccountName"]

        resp = self.v1_client.create_namespaced_pod(body=manifest,
                                                    namespace=namespace)
        LOG.info("Pod %(name)s created. Status: %(status)s" % {
            "name": name,
            "status": resp.status.phase
        })

    @atomic.action_timer("kube.create_emptydir_volume_pod_and_wait_running")
    def create_emptydir_volume_pod_and_wait_running(self, name, image,
                                                    mount_path,
                                                    namespace, sleep_time,
                                                    retries_total,
                                                    command=None):
        """Create pod with emptyDir volume, wait for running status.

        :param name: pod's name
        :param image: pod's image
        :param mount_path: pod's mount path of volume
        :param namespace: pod's namespace
        :param sleep_time: sleep time between each two retries
        :param retries_total: total number of retries
        :param command: array of strings representing container command
        :return: True if wait for running status successful and False otherwise
        """
        self.create_emptydir_volume_pod(
            name,
            image=image,
            mount_path=mount_path,
            namespace=namespace,
            command=command
        )

        i = 0
        flag = False
        while i < retries_total:
            LOG.debug("Attempt number %s" % i)
            resp = self.v1_client.read_namespaced_pod_status(
                name,
                namespace=namespace
            )

            if resp.status.phase == "Running":
                return True
            elif not flag:
                e_list = self.v1_client.list_namespaced_event(
                    namespace=namespace)
                for item in e_list.items:
                    if item.metadata.name.startswith(name):
                        if item.reason == "CreateContainerError":
                            LOG.error("Volume failed to mount to pod")
                            return False
                        elif (item.reason == "SuccessfulMountVolume" and
                              ("%s-volume" % name) in item.message):
                            LOG.info("Volume %s-volume successfully mount to "
                                     "pod %s" % (name, name))
                            flag = True
            i += 1
            commonutils.interruptable_sleep(sleep_time)
        return False

    @atomic.action_timer("kube.check_volume_pod_existence")
    def check_volume_pod_existence(self, name, namespace, check_cmd):
        """Exec check_cmd in pod and get response.

        :param name: pod's name
        :param namespace: pod's namespace
        :param check_cmd: check_cmd as array of strings
        """
        resp = stream(
            self.v1_client.connect_get_namespaced_pod_exec,
            name,
            namespace=namespace,
            command=check_cmd,
            stderr=True, stdin=False,
            stdout=True, tty=False)

        if "exec failed" in resp:
            LOG.error("Check command failed with error: %s" % resp)
            return False
        LOG.info("Check command return next response: '%s'" % resp)
        return True

    @atomic.action_timer("kube.create_secret_volume_pod")
    def create_secret_volume_pod(self, name, image, mount_path, namespace,
                                 command=None):
        """Create pod with secret volume.

        :param name: pod's name
        :param image: pod's image
        :param mount_path: pod's mount path of volume
        :param namespace: pod's namespace
        :param command: array of strings representing container command
        """
        container_spec = {
            "name": name,
            "image": image,
            "volumeMounts": [
                {
                    "mountPath": mount_path,
                    "name": "%s-volume" % name
                }
            ]
        }
        if command is not None and isinstance(command, (list, tuple)):
            container_spec["command"] = list(command)

        manifest = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {
                "name": name,
                "labels": {
                    "role": "rally-test"
                }
            },
            "spec": {
                "serviceAccountName": namespace,
                "containers": [container_spec],
                "volumes": [
                    {
                        "name": "%s-volume" % name,
                        "secret": {
                            "secretName": name
                        }
                    }
                ]
            }
        }

        if not self._spec.get("serviceaccounts"):
            del manifest["spec"]["serviceAccountName"]

        resp = self.v1_client.create_namespaced_pod(body=manifest,
                                                    namespace=namespace)
        LOG.info("Pod %(name)s created. Status: %(status)s" % {
            "name": name,
            "status": resp.status.phase
        })

    @atomic.action_timer("kube.create_secret_volume_pod_and_wait_running")
    def create_secret_volume_pod_and_wait_running(self, name, image,
                                                  mount_path,
                                                  namespace, sleep_time,
                                                  retries_total,
                                                  command=None):
        """Create pod with secret volume, wait for running status.

        :param name: pod's name
        :param image: pod's image
        :param mount_path: pod's mount path of volume
        :param namespace: pod's namespace
        :param sleep_time: sleep time between each two retries
        :param retries_total: total number of retries
        :param command: array of strings representing container command
        :return: True if wait for running status successful and False otherwise
        """
        self.create_secret_volume_pod(
            name,
            image=image,
            mount_path=mount_path,
            namespace=namespace,
            command=command
        )

        i = 0
        flag = False
        while i < retries_total:
            LOG.debug("Attempt number %s" % i)
            resp = self.v1_client.read_namespaced_pod_status(
                name,
                namespace=namespace
            )

            if resp.status.phase == "Running":
                return True
            elif not flag:
                e_list = self.v1_client.list_namespaced_event(
                    namespace=namespace
                )
                for item in e_list.items:
                    if item.metadata.name.startswith(name):
                        if item.reason == "CreateContainerError":
                            LOG.error("Volume failed to mount to pod")
                            return False
                        elif (item.reason == "SuccessfulMountVolume" and
                              ("%s-volume" % name) in item.message):
                            LOG.info("Volume %s-volume successfully mount to "
                                     "pod %s" % (name, name))
                            flag = True
            i += 1
            commonutils.interruptable_sleep(sleep_time)
        return False

    @atomic.action_timer("kube.create_hostpath_volume_pod")
    def create_hostpath_volume_pod(self, name, image, mount_path, volume_type,
                                   volume_path, namespace, command=None):
        """Create pod with hostPath volume.

        :param name: pod's name
        :param image: pod's image
        :param mount_path: pod's mount path of volume
        :param volume_path: hostPath volume path in host
        :param volume_type: hostPath type according to Kubernetes docs
        :param namespace: pod's namespace
        :param command: array of strings representing container command
        """
        container_spec = {
            "name": name,
            "image": image,
            "volumeMounts": [
                {
                    "mountPath": mount_path,
                    "name": "%s-volume" % name
                }
            ]
        }
        if command is not None and isinstance(command, (list, tuple)):
            container_spec["command"] = list(command)

        manifest = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {
                "name": name,
                "labels": {
                    "role": "rally-test"
                }
            },
            "spec": {
                "serviceAccountName": namespace,
                "containers": [container_spec],
                "volumes": [
                    {
                        "name": "%s-volume" % name,
                        "hostPath": {
                            "path": volume_path,
                            "type": volume_type
                        }
                    }
                ]
            }
        }

        if not self._spec.get("serviceaccounts"):
            del manifest["spec"]["serviceAccountName"]

        resp = self.v1_client.create_namespaced_pod(body=manifest,
                                                    namespace=namespace)
        LOG.info("Pod %(name)s created. Status: %(status)s" % {
            "name": name,
            "status": resp.status.phase
        })

    @atomic.action_timer("kube.create_hostpath_volume_pod_and_wait_running")
    def create_hostpath_volume_pod_and_wait_running(self, name, image,
                                                    mount_path,
                                                    volume_path, volume_type,
                                                    namespace, sleep_time,
                                                    retries_total,
                                                    command=None):
        """Create pod with secret volume, wait for running status.

        :param name: pod's name
        :param image: pod's image
        :param mount_path: pod's mount path of volume
        :param volume_path: hostPath volume path in host
        :param volume_type: hostPath type according to Kubernetes docs
        :param namespace: pod's namespace
        :param sleep_time: sleep time between each two retries
        :param retries_total: total number of retries
        :param command: array of strings representing container command
        :return: True if wait for running status successful and False otherwise
        """
        self.create_hostpath_volume_pod(
            name,
            image=image,
            mount_path=mount_path,
            volume_type=volume_type,
            volume_path=volume_path,
            namespace=namespace,
            command=command
        )

        i = 0
        flag = False
        while i < retries_total:
            LOG.debug("Attempt number %s" % i)
            resp = self.v1_client.read_namespaced_pod_status(
                name,
                namespace=namespace
            )

            if resp.status.phase == "Running":
                return True
            elif not flag:
                e_list = self.v1_client.list_namespaced_event(
                    namespace=namespace
                )
                for item in e_list.items:
                    if item.metadata.name.startswith(name):
                        if item.reason == "CreateContainerError":
                            LOG.error("Volume failed to mount to pod")
                            return False
                        elif (item.reason == "SuccessfulMountVolume" and
                              ("%s-volume" % name) in item.message):
                            LOG.info("Volume %s-volume successfully mount to "
                                     "pod %s" % (name, name))
                            flag = True
            i += 1
            commonutils.interruptable_sleep(sleep_time)
        return False

    @atomic.action_timer("kube.create_local_storageclass")
    def create_local_storageclass(self, name):
        manifest = {
            "kind": "StorageClass",
            "apiVersion": "storage.k8s.io/v1",
            "metadata": {
                "name": name,
                "labels": {
                    "role": "rally-test"
                }
            },
            "provisioner": "kubernetes.io/no-provisioner",
            "volumeBindingMode": "WaitForFirstConsumer"
        }

        self.v1_storage.create_storage_class(body=manifest)

        LOG.info("Local storage class %s created." % name)

    @atomic.action_timer("kube.delete_local_storageclass")
    def delete_local_storageclass(self, name):
        resp = self.v1_storage.delete_storage_class(
            name=name,
            body=k8s_config.V1DeleteOptions()
        )
        LOG.info("Local storage class %s delete started. "
                 "Status: %s" % (name, resp.status))

    @atomic.action_timer("kube.create_local_persistent_volume")
    def create_local_pv(self, name, storage_class, size, volume_mode,
                        local_path, access_modes, node_affinity, sleep_time,
                        retries_total):
        manifest = {
            "kind": "PersistentVolume",
            "apiVersion": "v1",
            "metadata": {
                "name": name,
                "labels": {
                    "role": "rally-test"
                }
            },
            "spec": {
                "capacity": {
                    "storage": size
                },
                "volumeMode": volume_mode,
                "accessModes": access_modes,
                "persistentVolumeReclaimPolicy": "Retain",
                "storageClassName": storage_class,
                "local": {
                    "path": local_path
                },
                "nodeAffinity": node_affinity
            }
        }

        resp = self.v1_client.create_persistent_volume(body=manifest)

        LOG.info("Local persistent volume %s create started. "
                 "Status: %s" % (name, resp.status))

        i = 0
        while i < retries_total:
            LOG.debug("Attempt number %s" % i)
            resp = self.v1_client.read_persistent_volume(name)
            if resp.status.phase not in ("Available", "Released"):
                i += 1
                commonutils.interruptable_sleep(sleep_time)
            else:
                return True
        return False

    @atomic.action_timer("kube.get_local_persistent_volume")
    def get_local_pv(self, name):
        return self.v1_client.read_persistent_volume(name)

    @atomic.action_timer("kube.delete_local_persistent_volume")
    def delete_local_pv(self, name, sleep_time, retries_total):
        resp = self.v1_client.delete_persistent_volume(
            name=name,
            body=k8s_config.V1DeleteOptions()
        )

        LOG.info("Local persistent volume %s delete started. "
                 "Status: %s" % (name, resp.status))

        i = 0
        while i < retries_total:
            LOG.debug("Attempt number %s" % i)
            try:
                self.v1_client.read_persistent_volume(name)
            except Exception:
                return True
            else:
                commonutils.interruptable_sleep(sleep_time)
                i += 1
        return False

    @atomic.action_timer("kube.create_local_persistent_volume_claim")
    def create_local_pvc(self, name, storage_class, access_modes, size,
                         namespace):
        manifest = {
            "kind": "PersistentVolumeClaim",
            "apiVersion": "v1",
            "metadata": {
                "name": name,
                "labels": {
                    "role": "rally-test"
                }
            },
            "spec": {
                "resources": {
                    "requests": {
                      "storage": size
                    }
                },
                "accessModes": access_modes,
                "storageClassName": storage_class
            }
        }

        resp = self.v1_client.create_namespaced_persistent_volume_claim(
            namespace=namespace,
            body=manifest
        )

        LOG.info("Local persistent volume claim %s create started. "
                 "Status: %s" % (name, resp.status))

    @atomic.action_timer("kube.get_local_pvc")
    def get_local_pvc(self, name, namespace):
        return self.v1_client.read_namespaced_persistent_volume_claim(
            name, namespace=namespace)

    @atomic.action_timer("kube.delete_local_pvc")
    def delete_local_pvc(self, name, namespace, sleep_time, retries_total):
        resp = self.v1_client.delete_namespaced_persistent_volume_claim(
            name=name,
            namespace=namespace,
            body=k8s_config.V1DeleteOptions()
        )

        LOG.info("Local persistent volume claim %s delete started. "
                 "Status: %s" % (name, resp.status))

        i = 0
        while i < retries_total:
            LOG.debug("Attempt number %s" % i)
            try:
                self.v1_client.read_namespaced_persistent_volume_claim(
                    name,
                    namespace=namespace
                )
            except Exception:
                return True
            else:
                commonutils.interruptable_sleep(sleep_time)
                i += 1
        return False

    @atomic.action_timer("kube.create_local_pvc_pod")
    def create_local_pvc_pod(self, name, image, mount_path, namespace,
                             command=None):
        """Create pod with emptyDir volume.

        :param name: pod's name
        :param image: pod's image
        :param mount_path: pod's mount path of volume
        :param namespace: pod's namespace
        :param command: array of strings representing container command
        """
        container_spec = {
            "name": name,
            "image": image,
            "volumeMounts": [
                {
                    "mountPath": mount_path,
                    "name": "%s-volume" % name
                }
            ]
        }
        if command is not None and isinstance(command, (list, tuple)):
            container_spec["command"] = list(command)

        manifest = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {
                "name": name,
                "labels": {
                    "role": "rally-test"
                }
            },
            "spec": {
                "serviceAccountName": namespace,
                "containers": [container_spec],
                "volumes": [
                    {
                        "name": "%s-volume" % name,
                        "persistentVolumeClaim": {
                            "claimName": name
                        }
                    }
                ]
            }
        }

        if not self._spec.get("serviceaccounts"):
            del manifest["spec"]["serviceAccountName"]

        resp = self.v1_client.create_namespaced_pod(body=manifest,
                                                    namespace=namespace)
        LOG.info("Pod %(name)s created. Status: %(status)s" % {
            "name": name,
            "status": resp.status.phase
        })

    @atomic.action_timer("kube.create_local_pvc_pod_and_wait_running")
    def create_local_pvc_pod_and_wait_running(self, name, namespace, image,
                                              mount_path, sleep_time,
                                              retries_total, command=None):
        self.create_local_pvc_pod(
            name,
            image=image,
            namespace=namespace,
            mount_path=mount_path,
            command=command
        )

        i = 0
        flag = False
        while i < retries_total:
            LOG.debug("Attempt number %s" % i)
            resp = self.v1_client.read_namespaced_pod_status(
                name,
                namespace=namespace
            )

            if resp.status.phase == "Running":
                return True
            elif not flag:
                e_list = self.v1_client.list_namespaced_event(
                    namespace=namespace
                )
                for item in e_list.items:
                    if item.metadata.name.startswith(name):
                        if item.reason == "CreateContainerError":
                            LOG.error("Volume failed to mount to pod")
                            return False
                        elif (item.reason == "SuccessfulMountVolume" and
                              ("%s-volume" % name) in item.message):
                            LOG.info("Volume %s-volume successfully mount to "
                                     "pod %s" % (name, name))
                            flag = True
            i += 1
            commonutils.interruptable_sleep(sleep_time)
        return False

    @atomic.action_timer("kube.create_configmap")
    def create_configmap(self, name, namespace, data):
        manifest = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {
                "name": name,
                "labels": {
                    "role": "rally-test"
                }
            },
            "data": data
        }
        self.v1_client.create_namespaced_config_map(namespace=namespace,
                                                    body=manifest)

    @atomic.action_timer("kube.create_configmap_volume_pod")
    def create_configmap_volume_pod(self, name, image, mount_path, namespace,
                                    command=None, subpath=None):
        """Create pod with hostPath volume.

        :param name: pod's name
        :param image: pod's image
        :param configmap: configMap name as a pod volume
        :param subpath: subPath from configMap data to mount in pod
        :param mount_path: pod's mount path of volume
        :param namespace: pod's namespace
        :param command: array of strings representing container command
        """
        container_spec = {
            "name": name,
            "image": image,
            "volumeMounts": [
                {
                    "mountPath": mount_path,
                    "name": "%s-volume" % name
                }
            ]
        }
        if command is not None and isinstance(command, (list, tuple)):
            container_spec["command"] = list(command)
        if subpath:
            container_spec["volumeMounts"][0]["subPath"] = subpath

        manifest = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {
                "name": name,
                "labels": {
                    "role": "rally-test"
                }
            },
            "spec": {
                "serviceAccountName": namespace,
                "containers": [container_spec],
                "volumes": [
                    {
                        "name": "%s-volume" % name,
                        "configMap": {
                            "name": name
                        }
                    }
                ]
            }
        }

        if not self._spec.get("serviceaccounts"):
            del manifest["spec"]["serviceAccountName"]

        resp = self.v1_client.create_namespaced_pod(body=manifest,
                                                    namespace=namespace)
        LOG.info("Pod %(name)s created. Status: %(status)s" % {
            "name": name,
            "status": resp.status.phase
        })

    @atomic.action_timer("kube.create_configmap_volume_pod_and_wait_running")
    def create_configmap_volume_pod_and_wait_running(self, name, image,
                                                     mount_path,
                                                     namespace, sleep_time,
                                                     retries_total,
                                                     command=None,
                                                     subpath=None):
        """Create pod with secret volume, wait for running status.

        :param name: pod's name
        :param image: pod's image
        :param mount_path: pod's mount path of volume
        :param subpath: subPath from configMap data to mount in pod
        :param namespace: pod's namespace
        :param sleep_time: sleep time between each two retries
        :param retries_total: total number of retries
        :param command: array of strings representing container command
        :return: True if wait for running status successful and False otherwise
        """
        self.create_configmap_volume_pod(
            name,
            image=image,
            mount_path=mount_path,
            subpath=subpath,
            namespace=namespace,
            command=command
        )

        i = 0
        flag = False
        while i < retries_total:
            LOG.debug("Attempt number %s" % i)
            resp = self.v1_client.read_namespaced_pod_status(
                name,
                namespace=namespace
            )

            if resp.status.phase == "Running":
                return True
            elif not flag:
                e_list = self.v1_client.list_namespaced_event(
                    namespace=namespace
                )
                for item in e_list.items:
                    if item.metadata.name.startswith(name):
                        if item.reason == "CreateContainerError":
                            LOG.error("Volume failed to mount to pod")
                            return False
                        elif (item.reason == "SuccessfulMountVolume" and
                              ("%s-volume" % name) in item.message):
                            LOG.info("Volume %s-volume successfully mount to "
                                     "pod %s" % (name, name))
                            flag = True
            i += 1
            commonutils.interruptable_sleep(sleep_time)
        return False

    @atomic.action_timer("kube.delete_configmap")
    def delete_configmap(self, name, namespace):
        self.v1_client.delete_namespaced_config_map(
            name, namespace=namespace,
            body=k8s_config.V1DeleteOptions()
        )

    @atomic.action_timer("kubernetes.get_replicaset")
    def get_replicaset(self, name, namespace, **kwargs):
        return self.v1beta1_ext.read_namespaced_replica_set(
            name=name,
            namespace=namespace
        )

    @atomic.action_timer("kubernetes.create_replicaset")
    def create_replicaset(self, name, namespace, replicas, image,
                          command=None, status_wait=True):
        """Create replicaset and wait until it won't be ready.

        :param name: replicaset name
        :param namespace: replicaset namespace
        :param replicas: number of replicaset replicas
        :param image: container's template image
        :param command: container's template array of strings command
        :param status_wait: wait for readiness if True
        """
        app = self.generate_random_name()
        name = name or self.generate_random_name()

        container_spec = {
            "name": name,
            "image": image
        }
        if command is not None and isinstance(command, (list, tuple)):
            container_spec["command"] = list(command)

        manifest = {
            "apiVersion": "extensions/v1beta1",
            "kind": "ReplicaSet",
            "metadata": {
                "name": name,
                "labels": {
                    "app": app
                }
            },
            "spec": {
                "replicas": replicas,
                "selector": {
                    "matchLabels": {
                        "app": app
                    }
                },
                "template": {
                    "metadata": {
                        "name": name,
                        "labels": {
                            "app": app
                        }
                    },
                    "spec": {
                        "serviceAccountName": namespace,
                        "containers": [container_spec]
                    }
                }
            }
        }

        if not self._spec.get("serviceaccounts"):
            del manifest["spec"]["template"]["spec"]["serviceAccountName"]

        self.v1beta1_ext.create_namespaced_replica_set(
            namespace=namespace,
            body=manifest
        )

        if status_wait:
            with atomic.ActionTimer(
                    self,
                    "kubernetes.wait_for_replicaset_become_ready"):
                wait_for_ready_replicas(
                    name,
                    read_method=self.get_replicaset,
                    replicas=replicas,
                    namespace=namespace)
        return name

    @atomic.action_timer("kubernetes.scale_replicaset")
    def scale_replicaset(self, name, namespace, replicas, status_wait=True):
        self.v1beta1_ext.patch_namespaced_replica_set(
            name=name,
            namespace=namespace,
            body={"spec": {"replicas": replicas}}
        )
        if status_wait:
            with atomic.ActionTimer(
                    self,
                    "kubernetes.wait_for_replicaset_scale"):
                wait_for_ready_replicas(
                    name,
                    read_method=self.get_replicaset,
                    replicas=replicas,
                    namespace=namespace)

    @atomic.action_timer("kubernetes.delete_replicaset")
    def delete_replicaset(self, name, namespace, status_wait=True):
        """Delete replicaset and optionally wait for termination

        :param name: replicaset name
        :param namespace: replicaset namespace
        :param status_wait: wait for termination if True
        """
        self.v1beta1_ext.delete_namespaced_replica_set(
            name=name,
            namespace=namespace,
            body=k8s_config.V1DeleteOptions()
        )
        if status_wait:
            with atomic.ActionTimer(self,
                                    "kubernetes.wait_replicaset_termination"):
                wait_for_not_found(name,
                                   read_method=self.get_replicaset,
                                   namespace=namespace,
                                   replicas=True)

    @atomic.action_timer("kubernetes.get_deployment")
    def get_deployment(self, name, namespace, **kwargs):
        return self.v1beta1_ext.read_namespaced_deployment_status(
            name=name,
            namespace=namespace
        )

    @atomic.action_timer("kubernetes.create_deployment")
    def create_deployment(self, name, namespace, replicas, image,
                          resources=None, env=None, command=None,
                          status_wait=True):
        """Create replicaset and wait until it won't be ready.

        :param name: replicaset name
        :param namespace: replicaset namespace
        :param replicas: number of replicaset replicas
        :param image: container's template image
        :param resources: container's template resources requirements
        :param env: container's template env variables array
        :param command: container's template array of strings command
        :param status_wait: wait for readiness if True
        """
        app = self.generate_random_name()
        name = name or self.generate_random_name()

        container_spec = {
            "name": name,
            "image": image
        }
        if command is not None and isinstance(command, (list, tuple)):
            container_spec["command"] = list(command)
        if env is not None and isinstance(env, (list, tuple)):
            container_spec["env"] = list(env)
        if resources is not None and isinstance(resources, dict):
            container_spec["resources"] = resources

        manifest = {
            "apiVersion": "extensions/v1beta1",
            "kind": "Deployment",
            "metadata": {
                "name": name,
                "labels": {
                    "app": app
                }
            },
            "spec": {
                "replicas": replicas,
                "template": {
                    "metadata": {
                        "name": name,
                        "labels": {
                            "app": app
                        }
                    },
                    "spec": {
                        "serviceAccountName": namespace,
                        "containers": [container_spec]
                    }
                }
            }
        }

        if not self._spec.get("serviceaccounts"):
            del manifest["spec"]["template"]["spec"]["serviceAccountName"]

        self.v1beta1_ext.create_namespaced_deployment(
            namespace=namespace,
            body=manifest
        )

        if status_wait:
            with atomic.ActionTimer(
                    self,
                    "kubernetes.wait_for_deployment_become_ready"):
                wait_for_ready_replicas(
                    name,
                    read_method=self.get_deployment,
                    replicas=replicas,
                    namespace=namespace)
        return name

    @atomic.action_timer("kubernetes.rollout_deployment")
    def rollout_deployment(self, name, namespace, changes, replicas,
                           status_wait=True):
        """Patch deployment and optionally wait for status.

        :param name: deployment name
        :param namespace: deployment namespace
        :param changes: map of changes, where could be image, env or resources
               requirements
        :param replicas: deployment replicas for status
        :param status_wait: wait for status if True
        """
        deployment = self.get_deployment(name, namespace=namespace)
        if changes.get("image"):
            deployment.spec.template.spec.containers[0].image = (
                changes.get("image"))
        elif changes.get("env"):
            deployment.spec.template.spec.containers[0].env = (
                changes.get("env"))
        elif changes.get("resources"):
            deployment.spec.template.spec.containers[0].resources = (
                changes.get("resources"))
        else:
            raise exceptions.InvalidArgumentsException(
                message="'changes' argument is a map with allowed mutually "
                        "exclusive keys: image, env, resources."
            )

        self.v1beta1_ext.patch_namespaced_deployment(
            name=name,
            namespace=namespace,
            body=deployment
        )
        if status_wait:
            with atomic.ActionTimer(
                    self,
                    "kubernetes.wait_for_deployment_rollout"):
                wait_for_ready_replicas(
                    name,
                    read_method=self.get_deployment,
                    replicas=replicas,
                    namespace=namespace)

    @atomic.action_timer("kubernetes.delete_deployment")
    def delete_deployment(self, name, namespace, status_wait=True):
        """Delete deployment and optionally wait for termination

        :param name: deployment name
        :param namespace: deployment namespace
        :param status_wait: wait for termination if True
        """
        self.v1beta1_ext.delete_namespaced_deployment(
            name=name,
            namespace=namespace,
            body=k8s_config.V1DeleteOptions()
        )
        if status_wait:
            with atomic.ActionTimer(self,
                                    "kubernetes.wait_deployment_termination"):
                wait_for_not_found(name,
                                   read_method=self.get_deployment,
                                   namespace=namespace,
                                   replicas=True)

    @atomic.action_timer("kubernetes.get_statefulset")
    def get_statefulset(self, name, namespace):
        return self.v1_apps.read_namespaced_stateful_set(
            name,
            namespace=namespace
        )

    @atomic.action_timer("kubernetes.create_statefulset")
    def create_statefulset(self, name, namespace, replicas, image,
                           command=None, status_wait=True):
        """Create statefulset and optionally wait for ready replicas.

        :param name: statefulset custom name
        :param namespace: statefulset namespace
        :param replicas: statefulset number of replicas
        :param image: container's template image
        :param command: container's template array of strings command
        :param status_wait: wait for ready replicas if True
        """
        app = self.generate_random_name()
        name = name or self.generate_random_name()

        container_spec = {
            "name": name,
            "image": image
        }
        if command is not None and isinstance(command, (list, tuple)):
            container_spec["command"] = list(command)

        manifest = {
            "apiVersion": "apps/v1",
            "kind": "StatefulSet",
            "metadata": {
                "name": name,
                "labels": {
                    "app": app
                }
            },
            "spec": {
                "selector": {
                    "matchLabels": {
                        "app": app
                    }
                },
                "replicas": replicas,
                "template": {
                    "metadata": {
                        "name": name,
                        "labels": {
                            "app": app
                        }
                    },
                    "spec": {
                        "serviceAccountName": namespace,
                        "containers": [container_spec]
                    }
                }
            }
        }

        if not self._spec.get("serviceaccounts"):
            del manifest["spec"]["template"]["spec"]["serviceAccountName"]

        self.v1_apps.create_namespaced_stateful_set(
            namespace=namespace,
            body=manifest
        )

        if status_wait:
            with atomic.ActionTimer(
                    self,
                    "kubernetes.wait_statefulset_for_ready_replicas"):
                wait_for_ready_replicas(name,
                                        read_method=self.get_statefulset,
                                        resource_type="StatefulSet",
                                        replicas=replicas,
                                        namespace=namespace)
        return name

    @atomic.action_timer("kubernetes.scale_statefulset")
    def scale_statefulset(self, name, namespace, replicas,
                          status_wait=True):
        """Scale statefulset to scale_replicas and optionally wait for status.

        :param name: statefulset name
        :param namespace: statefulset namespace
        :param replicas: statefulset replicas scale to
        :param status_wait: wait for ready scaling if True
        """
        self.v1_apps.patch_namespaced_stateful_set(
            name,
            namespace=namespace,
            body={"spec": {"replicas": replicas}}
        )

        if status_wait:
            with atomic.ActionTimer(
                    self,
                    "kubernetes.wait_statefulset_for_ready_replicas"):
                wait_for_ready_replicas(name,
                                        read_method=self.get_statefulset,
                                        resource_type="StatefulSet",
                                        replicas=replicas,
                                        namespace=namespace)

    @atomic.action_timer("kubernetes.delete_statefulset")
    def delete_statefulset(self, name, namespace, status_wait=True):
        """Delete statefulset and optionally wait for termination.

        :param name: statefulset name
        :param namespace: statefulset namespace
        :param status_wait: wait for ready scaling if True
        """
        self.v1_apps.delete_namespaced_stateful_set(
            name,
            namespace=namespace,
            body=k8s_config.V1DeleteOptions()
        )

        if status_wait:
            with atomic.ActionTimer(
                    self,
                    "kubernetes.wait_statefulset_for_termination"):
                wait_for_not_found(name,
                                   read_method=self.get_statefulset,
                                   resource_type="StatefulSet",
                                   namespace=namespace)

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
import time

from kubernetes import config
from kubernetes import client
from kubernetes.client.apis import core_v1_api
from kubernetes.stream import stream
from rally.common import logging
from rally.common import utils as commonutils
from rally.task import atomic
from rally.task import service

LOG = logging.getLogger(__name__)


class KubernetesService(service.Service):

    def __init__(self, spec, name_generator=None, atomic_inst=None):
        super(KubernetesService, self).__init__(None,
                                                name_generator=name_generator,
                                                atomic_inst=atomic_inst)
        self._spec = spec
        apiclient = config.new_client_from_config(spec.get("config_file"))
        apiclient.configuration.assert_hostname = False
        self.api = core_v1_api.CoreV1Api(api_client=apiclient)
        self.events = []

    @atomic.action_timer("kube.create_namespace")
    def create_namespace(self, name):
        """Create namespace.

        :param name: namespace name
        """
        manifest = {
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {
                "name": name,
                "labels": {
                    "role": "rally-test"
                }
            }
        }
        self.api.create_namespace(body=manifest)
        LOG.info("Namespace %s created" % name)

    @atomic.action_timer("create_namespace_and_wait_active_status")
    def create_namespace_and_wait_active(self, name, sleep_time=5,
                                         retries_total=30):
        """Create namespace and wait until status phase won't be Active.

        :param name: namespace name
        :param sleep_time: sleep time between each two retries
        :param retries_total: total number of retries
        :return: True if create successful and False otherwise
        """
        self.create_namespace(name)

        i = 0
        LOG.debug("Wait until namespace status won't be active")
        while i < retries_total:
            LOG.debug("Attempt number %s" % i)
            try:
                resp = self.api.read_namespace(name=name)
            except Exception as ex:
                LOG.warning("Unable to read namespace status: %s" % ex.message)
                i += 1
                commonutils.interruptable_sleep(sleep_time)
            else:
                if resp.status.phase != "Active":
                    i += 1
                    commonutils.interruptable_sleep(sleep_time)
                else:
                    return True
        return False

    @atomic.action_timer("kube.create_serviceaccount")
    def create_serviceaccount(self, name, namespace):
        """ Create serviceaccount and token for namespace.

        :param name: serviceaccount name
        :param namespace: namespace where sa should be created.
        """
        sa_manifest = {
            "apiVersion": "v1",
            "kind": "ServiceAccount",
            "metadata": {
                "name": name,
                "labels": {
                    "role": "rally-test"
                }
            }
        }
        self.api.create_namespaced_service_account(namespace=namespace,
                                                   body=sa_manifest)
        LOG.info("ServiceAccount %s created." % name)
        secret_manifest = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {
                "name": name,
                "labels": {
                    "role": "rally-test"
                },
                "annotations": {
                    "kubernetes.io/service-account.name": name
                }
            }
        }
        self.api.create_namespaced_secret(namespace=namespace,
                                          body=secret_manifest)
        LOG.info("Secret %s for service account created." % name)

    @atomic.action_timer("kube.create_secret")
    def create_secret(self, name, namespace):
        secret_manifest = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {
                "name": name,
                "labels": {
                    "role": "rally-test"
                }
            }
        }
        self.api.create_namespaced_secret(namespace=namespace,
                                          body=secret_manifest)
        LOG.info("Secret %s created." % name)

    def _update_pod_stats(self, name, conditions):
        """Method for collecting pods statuses: inited, scheduled, ready."""

        def to_time(dt):
            return time.mktime(dt)

        start, finish = None, None
        stat_dict = {
            "kube.initialized_pod": {},
            "kube.scheduled_pod": {},
            "kube.created_pod": {}
        }
        for d in conditions:
            if d.type == "Initialized":
                start = init_time = to_time(d.last_transition_time.timetuple())
                stat_dict["kube.initialized_pod"].update({
                    "started_at": init_time
                })
            elif d.type == "PodScheduled":
                scheduled = to_time(d.last_transition_time.timetuple())
                stat_dict["kube.scheduled_pod"].update({
                    "started_at": scheduled
                })
                stat_dict["kube.initialized_pod"].update({
                    "finished_at": scheduled
                })
            elif d.type == "Ready":
                finish = to_time(d.last_transition_time.timetuple())
                stat_dict["kube.created_pod"].update({
                    "started_at": start,
                    "finished_at": finish
                })
                stat_dict["kube.scheduled_pod"].update({
                    "finished_at": finish
                })
        self.events.extend([{
            "name": k,
            "started_at": v["started_at"],
            "finished_at": v["finished_at"]}
            for k, v in stat_dict.items()
        ])

    @atomic.action_timer("kube.create_pod")
    def create_pod(self, name, image, namespace, sleep_time=5,
                   retries_total=30):
        """Create pod in defined namespace.

        :param name: pod's name
        :param image: pod's image
        :param namespace: defined namespace to create pod in
        :param sleep_time: sleep time between each two retries
        :param retries_total: total number of retries
        :return: True if create started and False otherwise
        """
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
                "containers": [
                    {
                        "name": name,
                        "image": image
                    }
                ]
            }
        }

        if not self._spec.get("serviceaccounts"):
            del manifest["spec"]["serviceAccountName"]

        i = 0
        create_started = False
        while i < retries_total:
            LOG.debug("Attempt number %s" % i)
            try:
                resp = self.api.create_namespaced_pod(body=manifest,
                                                      namespace=namespace)
                LOG.info("Pod %(name)s created. Status: %(status)s" % {
                    "name": name,
                    "status": resp.status.phase
                })
            except Exception as ex:
                LOG.error("Pod create failed: %s" % ex.message)
                i += 1
                commonutils.interruptable_sleep(sleep_time)
            else:
                create_started = True
                break

        if not create_started:
            return False

        i = 0
        LOG.debug("Wait until pod status not running")
        while i < retries_total:
            LOG.debug("Attempt number %s" % i)
            try:
                resp = self.api.read_namespaced_pod(name=name,
                                                    namespace=namespace)
            except Exception as ex:
                LOG.warning("Unable to read pod status: %s" % ex.message)
                i += 1
                commonutils.interruptable_sleep(sleep_time)
            else:
                if resp.status.phase != "Running":
                    i += 1
                    commonutils.interruptable_sleep(sleep_time)
                else:
                    self._update_pod_stats(name, resp.status.conditions)
                    return True
        return False

    @atomic.action_timer("kube.create_replication_controller")
    def create_rc(self, name, replicas, image, namespace, sleep_time=5,
                  retries_total=30):
        """Create RC and wait until it won't be running.

        :param name: replication controller name
        :param replicas: number of replicas
        :param image: image for each replica
        :param namespace: replication controller namespace
        :param sleep_time: sleep time between each two retries
        :param retries_total: total number of retries
        :return: True if create finished successfully and False otherwise
        """

        app = self.generate_random_name().replace("_", "-").lower()
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
                        "containers": [
                            {
                                "name": name,
                                "image": image
                            }
                        ]
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
                self.api.create_namespaced_replication_controller(
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
                resp = self.api.read_namespaced_replication_controller(
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
        resp = self.api.read_namespaced_replication_controller(
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
        self.api.patch_namespaced_replication_controller(
            name=name,
            namespace=namespace,
            body={"spec": {"replicas": replicas}}
        )
        i = 0
        LOG.debug("Wait until RC pods won't be ready")
        while i < retries_total:
            LOG.debug("Attempt number %s" % i)
            try:
                resp = self.api.read_namespaced_replication_controller(
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

    @atomic.action_timer("kube.list_namespaces")
    def list_namespaces(self):
        """List namespaces."""
        try:
            self.api.list_namespace()
        except Exception:
            return False
        return True

    @atomic.action_timer("kube.delete_replication_controller")
    def delete_rc(self, name, namespace, sleep_time=5, retries_total=30):
        """Delete RC from namespace and wait until it won't be terminated.

        :param name: replication controller name
        :param namespace: namespace name of defined RC
        :param sleep_time: sleep time between each two retries
        :param retries_total: total number of retries
        :returns True if delete successful and False otherwise
        """
        resp = self.api.delete_namespaced_replication_controller(
            name=name, namespace=namespace, body=client.V1DeleteOptions())
        LOG.info("RC %(name)s delete started. Status: %(status)s" % {
            "name": name,
            "status": resp.status
        })

        i = 0
        while i < retries_total:
            LOG.debug("Attempt number %s" % i)
            try:
                self.api.read_namespaced_replication_controller_status(
                    name=name, namespace=namespace)
            except Exception:
                return True
            else:
                commonutils.interruptable_sleep(sleep_time)
                i += 1
        return False

    @atomic.action_timer("kube.delete_pod")
    def delete_pod(self, name, namespace, sleep_time=5, retries_total=30):
        """Delete pod from namespace.

        :param name: pod's name
        :param namespace: pod's namespace
        :param sleep_time: sleep time between each two retries
        :param retries_total: total number of retries
        :returns True if delete successful and False otherwise
        """
        resp = self.api.delete_namespaced_pod(name=name, namespace=namespace,
                                              body=client.V1DeleteOptions())
        LOG.info("Pod %(name)s delete started. Status: %(status)s" % {
            "name": name,
            "status": resp.status
        })

        i = 0
        while i < retries_total:
            LOG.debug("Attempt number %s" % i)
            try:
                self.api.read_namespaced_pod_status(name=name,
                                                    namespace=namespace)
            except Exception:
                return True
            else:
                commonutils.interruptable_sleep(sleep_time)
                i += 1
        return False

    @atomic.action_timer("kube.delete_namespace")
    def delete_namespace(self, name):
        """Delete namespace.

        :param name: namespace name
        """
        resp = self.api.delete_namespace(name=name,
                                         body=client.V1DeleteOptions())

        LOG.info("Namespace %(name)s deleted. Status: %(status)s" % {
            "name": name,
            "status": resp.status
        })

    @atomic.action_timer("kube.delete_namespace_and_wait_termination")
    def delete_namespace_and_wait_termination(self, name, sleep_time=5,
                                              retries_total=30):
        """Delete namespace and wait it's full termination.

        :param name: namespace name
        :param sleep_time: sleep time between each two retries
        :param retries_total: total number of retries
        :return: True if termination successful and False otherwise
        """
        self.delete_namespace(name)
        i = 0
        while i < retries_total:
            LOG.debug("Attempt number %s" % i)
            try:
                self.api.read_namespace(name)
            except Exception:
                return True
            else:
                commonutils.interruptable_sleep(sleep_time)
                i += 1
        return False

    @atomic.action_timer("kube.create_emptydir_volume_pod")
    def create_emptydir_volume_pod(self, name, image, mount_path, namespace):
        """Create pod with emptyDir volume.

        :param name: pod's name
        :param image: pod's image
        :param mount_path: pod's mount path of volume
        :param namespace: pod's namespace
        """
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
                "containers": [
                    {
                        "name": name,
                        "image": image,
                        "volumeMounts": [
                            {
                                "mountPath": mount_path,
                                "name": "%s-volume" % name
                            }
                        ]
                    }
                ],
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

        resp = self.api.create_namespaced_pod(body=manifest,
                                              namespace=namespace)
        LOG.info("Pod %(name)s created. Status: %(status)s" % {
            "name": name,
            "status": resp.status.phase
        })

    @atomic.action_timer("kube.create_emptydir_volume_pod_and_wait_running")
    def create_emptydir_volume_pod_and_wait_running(self, name, image,
                                                    mount_path,
                                                    namespace, sleep_time,
                                                    retries_total):
        """Create pod with emptyDir volume, wait for running status.

        :param name: pod's name
        :param image: pod's image
        :param mount_path: pod's mount path of volume
        :param namespace: pod's namespace
        :param sleep_time: sleep time between each two retries
        :param retries_total: total number of retries
        :return: True if wait for running status successful and False otherwise
        """
        self.create_emptydir_volume_pod(
            name,
            image=image,
            mount_path=mount_path,
            namespace=namespace
        )

        i = 0
        flag = False
        while i < retries_total:
            LOG.debug("Attempt number %s" % i)
            resp = self.api.read_namespaced_pod_status(name,
                                                       namespace=namespace)

            if resp.status.phase == "Running":
                return True
            elif not flag:
                e_list = self.api.list_namespaced_event(namespace=namespace)
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
            self.api.connect_get_namespaced_pod_exec,
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
    def create_secret_volume_pod(self, name, image, mount_path, namespace):
        """Create pod with secret volume.

        :param name: pod's name
        :param image: pod's image
        :param mount_path: pod's mount path of volume
        :param namespace: pod's namespace
        """
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
                "containers": [
                    {
                        "name": name,
                        "image": image,
                        "volumeMounts": [
                            {
                                "mountPath": mount_path,
                                "name": "%s-volume" % name
                            }
                        ]
                    }
                ],
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

        resp = self.api.create_namespaced_pod(body=manifest,
                                              namespace=namespace)
        LOG.info("Pod %(name)s created. Status: %(status)s" % {
            "name": name,
            "status": resp.status.phase
        })

    @atomic.action_timer("kube.create_secret_volume_pod_and_wait_running")
    def create_secret_volume_pod_and_wait_running(self, name, image,
                                                  mount_path,
                                                  namespace, sleep_time,
                                                  retries_total):
        """Create pod with secret volume, wait for running status.

        :param name: pod's name
        :param image: pod's image
        :param mount_path: pod's mount path of volume
        :param namespace: pod's namespace
        :param sleep_time: sleep time between each two retries
        :param retries_total: total number of retries
        :return: True if wait for running status successful and False otherwise
        """
        self.create_secret_volume_pod(
            name,
            image=image,
            mount_path=mount_path,
            namespace=namespace
        )

        i = 0
        flag = False
        while i < retries_total:
            LOG.debug("Attempt number %s" % i)
            resp = self.api.read_namespaced_pod_status(name,
                                                       namespace=namespace)

            if resp.status.phase == "Running":
                return True
            elif not flag:
                e_list = self.api.list_namespaced_event(namespace=namespace)
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

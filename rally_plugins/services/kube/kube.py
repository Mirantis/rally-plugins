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

    @atomic.action_timer("kube.delete_pod")
    def delete_pod(self, name, namespace, sleep_time=5, retries_total=30):
        """Delete pod from namespace.

        :param name: pod's name
        :param namespace: pod's namespace
        :param sleep_time: sleep time between each two retries
        :param retries_total: total number of retries
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

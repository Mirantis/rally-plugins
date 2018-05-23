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

from kubernetes import config
from kubernetes import client
from kubernetes.client.apis import core_v1_api
from kubernetes.client import rest
from rally.common import logging
from rally.common import utils as commonutils
from rally.task import atomic
from rally.task import service

LOG = logging.getLogger(__name__)


class KubernetesService(service.Service):

    def __init__(self, name_generator=None, atomic_inst=None):
        super(KubernetesService, self).__init__(None,
                                                name_generator=name_generator,
                                                atomic_inst=atomic_inst)
        self.api = core_v1_api.CoreV1Api()

    @atomic.action_timer("kube.create_namespace")
    def create_namespace(self, name, sleep_time=1, retries_total=30):
        """Create namespace and wait until it's not active.

        :param name: namespace name
        :param sleep_time: sleep time between iterations of waiting
        :param retries_total: total count of retries before create failed
        :returns True if namespace created successfully and False otherwise
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
        resp = self.api.create_namespace(body=manifest)
        LOG.info("Namespace %(name)s created. Status: %(status)s" % {
            "name": name,
            "status": resp.status.phase
        })

        i = 0
        LOG.debug("Wait until namespace status not active")
        while i < retries_total:
            LOG.debug("Attempt number %s" % i)
            resp = self.api.read_namespace(name)
            if resp.status.phase != "Active":
                i += 1
                commonutils.interruptable_sleep(sleep_time)
            else:
                return True
        return False

    @atomic.action_timer("kube.create_pod")
    def create_pod(self, name, image, namespace, sleep_time=5,
                   retries_total=30):
        """Create pod in defined namespace.

        :param name: pod's name
        :param image: pod's image
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
                "containers": [
                    {
                        "name": name,
                        "image": image
                    }
                ]
            }
        }

        i = 0
        while i < retries_total:
            LOG.debug("Attempt number %s" % i)
            try:
                resp = self.api.create_namespaced_pod(body=manifest,
                                                      namespace=namespace)
                LOG.info("Pod %(name)s created. Status: %(status)s" % {
                    "name": name,
                    "status": resp.status.phase
                })
            except rest.ApiException as ex:
                LOG.error("Pod create failed with status %(status)s: %(msg)s" % {
                    "status": ex.status,
                    "msg": ex.message
                })
                i += 1
                commonutils.interruptable_sleep(sleep_time)
            else:
                return True
        return False

    @atomic.action_timer("kube.wait_pod_running")
    def wait_pod_running(self, name, namespace, sleep_time=1,
                         retries_total=30):
        """Wait until pod status not running.

        :param name: pod's name
        :param namespace: pod's namespace
        :param sleep_time: sleep time between requesting pod's status.
        :param retries_total: total count of retries before method failed.
        :return: True if pod status becomes 'Running' and False otherwise
        """
        i = 0
        LOG.debug("Wait until pod status not running")
        while i < retries_total:
            LOG.debug("Attempt number %s" % i)
            resp = self.api.read_namespaced_pod(name=name, namespace=namespace)
            if resp.status.phase != "Running":
                i += 1
                commonutils.interruptable_sleep(sleep_time)
            else:
                return True
        return False

    @atomic.action_timer("kube.delete_pod")
    def delete_pod(self, name, namespace):
        """Delete pod from namespace.

        :param name: pod's name
        :param namespace: pod's namespace
        """
        resp = self.api.delete_namespaced_pod(name=name, namespace=namespace,
                                              body=client.V1DeleteOptions())
        LOG.info("Pod %(name)s deleted. Status: %(status)s" % {
            "name": name,
            "status": resp.status
        })

    @atomic.action_timer("kube.delete_namespace")
    def delete_namespace(self, name):
        """Delete namespace.

        :param name: namespace name
        """
        resp = self.api.delete_namespace(name=name, body=client.V1DeleteOptions())
        LOG.info("Namespace %(name)s deleted. Status: %(status)s" % {
            "name": name,
            "status": resp.status
        })

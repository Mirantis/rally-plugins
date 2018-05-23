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

from rally.common import logging
from rally.task import scenario
from rally.task import types
from rally.task import utils
from rally.task import validation

from rally_openstack import consts
from rally_plugins.services.kube import kube

LOG = logging.getLogger(__name__)


@scenario.configure(name="Kubernetes.run_namespaced_pods",
                    platform="openstack")
class NamespacedPodsPlugin(scenario.Scenario):

    def _cleanup(self, client, pods, namespace):
        for pod in pods:
            client.delete_pod(pod, namespace=namespace)
        client.delete_namespace(namespace)

    def run(self, pods_number, image, sleep_time=5, retries_total=30):
        client = kube.KubernetesService(
            name_generator=self.generate_random_name,
            atomic_inst=self.atomic_actions()
        )

        namespace = self.generate_random_name().replace('_', '-').lower()
        self.assertTrue(client.create_namespace(namespace,
                                                sleep_time=sleep_time,
                                                retries_total=retries_total))
        LOG.info("Namespace %s is active" % namespace)

        pods = []
        for i in range(pods_number):
            pod_name = self.generate_random_name().replace('_', '-').lower()
            self.assertTrue(client.create_pod(pod_name, image=image,
                                              namespace=namespace,
                                              sleep_time=sleep_time,
                                              retries_total=retries_total))
            pods.append(pod_name)

        for pod in pods:
            self.assertTrue(client.wait_pod_running(
                pod, namespace=namespace, sleep_time=sleep_time,
                retries_total=retries_total))

        LOG.info("Cleanup pods and namespace")
        self._cleanup(client, pods, namespace)

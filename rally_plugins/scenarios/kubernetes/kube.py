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

from rally_plugins.scenarios.kubernetes import common


LOG = logging.getLogger(__name__)


@scenario.configure(name="Kubernetes.run_namespaced_pod",
                    platform="kubernetes")
class NamespacedPodPlugin(common.KubernetesScenario, scenario.Scenario):
    """Kubernetes pod create and delete test.

    Choose created namespace, create pod with defined image, wait until it
    not be running and delete it after.
    """

    def _make_event_data(self):
        data = [[] for _ in range(3)]
        state_map = {
            "kube.initialized_pod": 0,
            "kube.scheduled_pod": 1,
            "kube.created_pod": 2
        }

        for e in self.client.events:
            duration = e["finished_at"] - e["started_at"]
            data[state_map[e["name"]]] = [e["name"], duration]
        return data

    def run(self, image, sleep_time=5, retries_total=30):
        """Create pod and then delete it.

        :param image: image used in pods manifests
        :param sleep_time: sleep time between each two retries
        :param retries_total: total number of retries
        """
        namespace = self._choose_namespace()
        pod = self.generate_name()

        # create
        self.assertTrue(self.client.create_pod(pod, image=image,
                                               namespace=namespace,
                                               sleep_time=sleep_time,
                                               retries_total=retries_total))

        # cleanup
        self.assertTrue(self.client.delete_pod(pod, namespace=namespace,
                                               sleep_time=sleep_time,
                                               retries_total=retries_total))

        data = self._make_event_data()
        self.add_output(
            additive={"title": "Pod's conditions total duration",
                      "description": "Total durations for pod in each "
                                     "iteration",
                      "chart_plugin": "StackedArea",
                      "data": data,
                      "label": "Total seconds",
                      "axis_label": "Iteration"})


@scenario.configure(name="Kubernetes.create_delete_replication_controller")
class RCCreateAndDelete(common.KubernetesScenario, scenario.Scenario):
    """Kubernetes replication controller create and delete test.

    Choose created namespace, create RC with defined image and number of
    replicas, wait until it won't be running and delete it after.
    """

    def run(self, replicas, image, sleep_time=5, retries_total=30):
        namespace = self._choose_namespace()
        rc = self.generate_name()

        # create
        self.assertTrue(self.client.create_rc(rc, replicas=replicas,
                                              image=image, namespace=namespace,
                                              sleep_time=sleep_time,
                                              retries_total=retries_total))

        # cleanup
        self.assertTrue(self.client.delete_rc(rc, namespace=namespace,
                                              sleep_time=sleep_time,
                                              retries_total=retries_total))

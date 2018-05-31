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

import random

from rally.common import logging
from rally.task import scenario
from rally_plugins.services.kube import kube


LOG = logging.getLogger(__name__)


@scenario.configure(name="Kubernetes.run_namespaced_pod",
                    platform="kubernetes")
class NamespacedPodPlugin(scenario.Scenario):
    """Kubernetes pod create and delete test.

    Choose created namespace, create pod with defined image, wait until it
    not be running and delete it after.
    """

    def __init__(self, context=None):
        super(NamespacedPodPlugin, self).__init__(context)
        spec = {"namespaces": self.context.get("namespaces"),
                "serviceaccounts": self.context.get("serviceaccounts")}
        if "env" in self.context:
            spec.update(self.context["env"]["platforms"]["kubernetes"])
            self.client = kube.KubernetesService(
                spec,
                name_generator=self.generate_random_name,
                atomic_inst=self.atomic_actions())

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

    def _choose_namespace(self):
        if self.context["namespace_choice_method"] == "random":
            return random.choice(self.context["namespaces"])
        elif self.context["namespace_choice_method"] == "round_robin":
            idx = (self.context["iteration"] - 1)
            idx = idx % len(self.context["namespaces"])
            return self.context["namespaces"][idx]

    def run(self, image, sleep_time=5, retries_total=30):
        """Create pod and then delete it.

        :param image: image used in pods manifests
        :param sleep_time: sleep time between each two retries
        :param retries_total: total number of retries
        """
        namespace = self._choose_namespace()
        pod = self.generate_random_name().replace('_', '-').lower()

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

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

from rally.task import scenario

from rally_plugins.services.kube import kube


class KubernetesScenario(scenario.Scenario):

    def __init__(self, context=None):
        super(KubernetesScenario, self).__init__(context)
        spec = {"namespaces": self.context.get("namespaces"),
                "serviceaccounts": self.context.get("serviceaccounts")}
        if "env" in self.context:
            spec.update(self.context["env"]["platforms"]["kubernetes"])
            self.client = kube.KubernetesService(
                spec,
                name_generator=self.generate_random_name,
                atomic_inst=self.atomic_actions())

    def _choose_namespace(self):
        if self.context["namespace_choice_method"] == "random":
            return random.choice(self.context["namespaces"])
        elif self.context["namespace_choice_method"] == "round_robin":
            idx = (self.context["iteration"] - 1)
            idx = idx % len(self.context["namespaces"])
            return self.context["namespaces"][idx]

    def _choose_replication_controller(self):
        if self.context["rc_choice_method"] == "random":
            return random.choice(self.context["replication_controllers"])
        elif self.context["rc_choice_method"] == "round_robin":
            idx = (self.context["iteration"] - 1)
            idx = idx % len(self.context["replication_controllers"])
            return self.context["replication_controllers"][idx]

    def generate_name(self):
        return self.generate_random_name().replace('_', '-').lower()

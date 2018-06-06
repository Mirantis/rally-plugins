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

from rally.task import context
from rally.common import logging
from rally import consts

from rally_plugins.services.kube import kube

LOG = logging.getLogger(__name__)


@context.configure("kubernetes.replication_controllers", order=1002,
                   platform="kubernetes")
class KubernetesReplicationControllerContext(context.Context):
    """Context for creating RCs."""

    CONFIG_SCHEMA = {
        "type": "object",
        "$schema": consts.JSON_SCHEMA,
        "additionalProperties": False,
        "properties": {
            "count": {
                "type": "number"
            },
            "image": {
                "type": "string"
            },
            "replicas": {
                "type": "number"
            },
            "rc_choice_method": {
                "enum": ["random", "round_robin"]
            }
        }
    }

    DEFAULT_CONFIG = {"rc_choice_method": "random"}

    def __init__(self, ctx):
        super(KubernetesReplicationControllerContext, self).__init__(ctx)
        self.client = kube.KubernetesService(
            self.env["platforms"]["kubernetes"],
            name_generator=self.generate_random_name,
            atomic_inst=self.atomic_actions()
        )

    def _choose_namespace(self):
        if self.context.get("namespaces") is None:
            return
        if self.context["namespace_choice_method"] == "random":
            return random.choice(self.context["namespaces"])
        elif self.context["namespace_choice_method"] == "round_robin":
            idx = (self.context["iteration"] - 1)
            idx = idx % len(self.context["namespaces"])
            return self.context["namespaces"][idx]

    def setup(self):
        self.context.update({"rc_choice_method":
                             self.config["rc_choice_method"]})
        self.context.setdefault("replication_controllers", [])
        for _ in range(self.config.get("count")):
            new_name = self.generate_random_name().replace('_', '-').lower()
            namespace = self._choose_namespace()

            try:
                self.client.create_rc(new_name,
                                      namespace=namespace,
                                      replicas=self.config.get("replicas"),
                                      image=self.config.get("image"))
            except Exception as ex:
                LOG.error("Cannot create at least "
                          "one replication controller: %s" % ex.message)
                break

            self.context["replication_controllers"].append((new_name,
                                                            namespace))

    def cleanup(self):
        for name, namespace in self.context.get("replication_controllers"):
            self.client.delete_rc(name, namespace=namespace)

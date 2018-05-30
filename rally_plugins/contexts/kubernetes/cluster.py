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
from rally.task import context
from rally.common import logging
from rally import consts

from rally_plugins.services.kube import kube

LOG = logging.getLogger(__name__)


@context.configure("kubernetes.namespaces", order=1001, platform="kubernetes")
class KubernetesNamespaceContext(context.Context):
    """Context for creating namespaces (optionally with serviceaccount)."""

    CONFIG_SCHEMA = {
        "type": "object",
        "$schema": consts.JSON_SCHEMA,
        "additionalProperties": False,
        "properties": {
            "count": {
                "type": "number"
            },
            "with_serviceaccount": {
                "type": "boolean"
            },
            "namespace_choice_method": {
                "enum": ["random", "round_robin"]
            }
        }
    }

    DEFAULT_CONFIG = {"namespace_choice_method": "random"}

    def __init__(self, ctx):
        super(KubernetesNamespaceContext, self).__init__(ctx)
        self.client = kube.KubernetesService(
            self.env["platforms"]["kubernetes"],
            name_generator=self.generate_random_name,
            atomic_inst=self.atomic_actions()
        )

    def setup(self):
        self.context.update({"namespace_choice_method":
                             self.config["namespace_choice_method"]})
        self.context.setdefault("namespaces", [])
        for _ in range(self.config.get("count")):
            new_name = self.generate_random_name().replace('_', '-').lower()
            try:
                self.client.create_namespace(new_name)
            except Exception as ex:
                LOG.error("Cannot create at least "
                          "one namespace: %s" % ex.message)
                break
            self.context["namespaces"].append(new_name)
            if self.config.get("with_serviceaccount"):
                self.context["serviceaccounts"] = True
                self.client.create_serviceaccount(new_name, namespace=new_name)

    def cleanup(self):
        for name in self.context.get("namespaces"):
            self.client.delete_namespace(name)

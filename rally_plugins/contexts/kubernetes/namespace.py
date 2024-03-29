# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from rally.task import context
from rally.common import utils as commonutils

from rally_plugins.contexts.kubernetes import context as common_context


@context.configure("namespaces", order=1001, platform="kubernetes")
class NamespaceContext(common_context.BaseKubernetesContext):
    """Context for creating namespaces (optionally with service account)."""

    CONFIG_SCHEMA = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "count": {
                "type": "integer",
                "minimum": 1
            },
            "with_serviceaccount": {
                "type": "boolean"
            },
            "namespace_choice_method": {
                "enum": ["random", "round_robin"]
            },
            "serviceaccount_delay": {
                "type": "integer",
                "minimum": 0
            }
        }
    }

    DEFAULT_CONFIG = {"namespace_choice_method": "random"}

    def setup(self):
        self.context["kubernetes"].update({
            "namespace_choice_method": self.config["namespace_choice_method"],
            "serviceaccounts": self.config.get("with_serviceaccount") or False,
            "serviceaccount_delay": self.config.get("serviceaccount_delay") or 0
        })

        self.context["kubernetes"].setdefault("namespaces", [])
        for _ in range(self.config.get("count")):
            name = self.client.create_namespace(None, status_wait=False)
            self.context["kubernetes"]["namespaces"].append(name)
            if self.config.get("with_serviceaccount"):
                self.client.create_serviceaccount(name, namespace=name)
                self.client.create_secret(name, namespace=name)
                commonutils.interruptable_sleep(
                    self.context["kubernetes"]["serviceaccount_delay"]
                )

    def cleanup(self):
        for name in self.context["kubernetes"].get("namespaces"):
            self.client.delete_namespace(name)


@context.configure("kubernetes.namespaces", order=1001, platform="kubernetes")
class LegaceNamespaceContext(NamespaceContext):
    """[DEPRECATED] Use `namespace` context instead."""
    pass

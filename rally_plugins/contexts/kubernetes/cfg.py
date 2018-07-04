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

from rally.common import cfg
from rally.task import context

from rally_plugins.contexts.kubernetes import context as common_context

CONF = cfg.CONF


@context.configure("kubernetes.cfg", order=500, platform="kubernetes")
class CfgContext(common_context.BaseKubernetesContext):
    """Context to override kubernetes config opts. Only for rally-plugins."""

    CONFIG_SCHEMA = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "prepoll_delay": {
                "type": "number",
                "minimum": 0
            },
            "sleep_time": {
                "type": "number",
                "minimum": 0
            },
            "retries_total": {
                "type": "integer",
                "minimum": 1
            },
        }
    }

    def setup(self):
        self.context["kubernetes"] = {
            "sleep_time": CONF.kubernetes.status_poll_interval,
            "retries_total": CONF.kubernetes.status_total_retries,
            "prepoll_delay": CONF.kubernetes.start_prepoll_delay
        }

        if self.config.get("sleep_time"):
            CONF.set_override("status_poll_interval",
                              self.config["sleep_time"],
                              "kubernetes")
        if self.config.get("retries_total"):
            CONF.set_override("status_total_retries",
                              self.config["retries_total"],
                              "kubernetes")
        if self.config.get("prepoll_delay"):
            CONF.set_override("start_prepoll_delay",
                              self.config["prepoll_delay"],
                              "kubernetes")

    def cleanup(self):
        CONF.set_override("status_poll_interval",
                          self.context["kubernetes"]["sleep_time"],
                          "kubernetes")
        CONF.set_override("status_total_retries",
                          self.context["kubernetes"]["retries_total"],
                          "kubernetes")
        CONF.set_override("start_prepoll_delay",
                          self.context["kubernetes"]["prepoll_delay"],
                          "kubernetes")

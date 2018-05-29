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

from kubernetes import client
from kubernetes import config
from rally.task import context
from rally.common import logging
from rally import consts

LOG = logging.getLogger(__name__)


@context.configure("kubeconfig", order=1000)
class KubeConfigContext(context.Context):
    """Connect to kube cluster with specified file."""

    CONFIG_SCHEMA = {
        "type": "object",
        "$schema": consts.JSON_SCHEMA,
        "additionalProperties": False,
        "properties": {
            "config_file": {
                "type": "string"
            }
        }
    }

    def setup(self):
        config.load_kube_config(self.config.get("config_file"))

    def cleanup(self):
        pass

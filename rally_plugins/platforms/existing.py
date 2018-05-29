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

import json
import traceback

from kubernetes import config
from kubernetes.client.apis import core_v1_api
from kubernetes.client.apis import version_api
from rally.env import platform


@platform.configure(name="existing", platform="kubernetes")
class KubernetesPlatform(platform.Platform):
    """Default plugin for Kubernetes."""

    CONFIG_SCHEMA = {
        "type": "object",
        "properties": {
            "config_file": {
                "type": "string"
            }
        },
        "additionalProperties": False
    }

    def __init__(self, spec, **kwargs):
        super(KubernetesPlatform, self).__init__(spec, **kwargs)
        self._api = None

    def create(self):
        """Pass kubeconfig to internal Configuration."""
        return {"config_file": self.spec.get("config_file")}, {}

    def destroy(self):
        # NOTE(prazumovsky): No action need to be performed.
        pass

    def check_health(self):
        """Check whatever platform is alive."""
        try:
            api = config.new_client_from_config(self.spec.get("config_file"))
            core_v1_api.CoreV1Api(api_client=api).list_namespace()
        except Exception as ex:
            return {
                "available": False,
                "message": "Something went wrong: %s" % ex.message,
                "traceback": traceback.format_exc()
            }

        return {"available": True}

    def cleanup(self, task_uuid=None):
        return {
            "message": "Coming soon!",
            "discovered": 0,
            "deleted": 0,
            "failed": 0,
            "resources": {},
            "errors": []
        }

    def _get_validation_context(self):
        return {}

    def info(self):
        api = config.new_client_from_config(self.spec.get("config_file"))
        version = version_api.VersionApi(api).get_code().to_dict()
        return {"info": version}

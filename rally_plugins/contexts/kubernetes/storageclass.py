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

from rally.task import context
from rally.common import logging
from rally import consts

from rally_plugins.services.kube import kube

LOG = logging.getLogger(__name__)


@context.configure("kubernetes.local_storageclass", order=1002,
                   platform="kubernetes")
class KubernetesLocalStorageClassContext(context.Context):
    """Context for creating local storage classes."""

    CONFIG_SCHEMA = {
        "type": "object",
        "$schema": consts.JSON_SCHEMA,
        "additionalProperties": False,
        "properties": {}
    }

    def __init__(self, ctx):
        super(KubernetesLocalStorageClassContext, self).__init__(ctx)
        self.client = kube.KubernetesService(
            self.env["platforms"]["kubernetes"],
            name_generator=self.generate_random_name,
            atomic_inst=self.atomic_actions()
        )

    def setup(self):
        self.context.setdefault("storageclass", None)

        name = self.generate_random_name().replace('_', '-').lower()

        try:
            self.client.create_local_storageclass(name)
        except Exception as ex:
            LOG.error("Cannot create local storageclass: %s" % ex)
            return
        self.context["storageclass"] = name

    def cleanup(self):
        self.client.delete_local_storageclass(self.context["storageclass"])

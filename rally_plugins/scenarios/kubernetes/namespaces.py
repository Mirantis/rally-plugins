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


@scenario.configure(name="Kubernetes.create_delete_namespace",
                    platform="kubernetes")
class NamespaceCreateDelete(common.KubernetesScenario, scenario.Scenario):
    """Create and delete namespace.

    Test creates namespace, wait until it won't be active and then delete it.
    """

    def run(self, sleep_time, retries_total):
        """Create and delete namespace with random name.

        :param sleep_time: sleep time between each two retries
        :param retries_total: total number of retries
        """
        namespace = self.generate_name()

        # create
        self.assertTrue(self.client.create_namespace_and_wait_active(
            namespace,
            sleep_time=sleep_time,
            retries_total=retries_total
        ))

        # delete
        self.assertTrue(self.client.delete_namespace_and_wait_termination(
            namespace,
            sleep_time=sleep_time,
            retries_total=retries_total
        ))


@scenario.configure(name="Kubernetes.list_namespaces", platform="kubernetes")
class ListNamespaces(common.KubernetesScenario, scenario.Scenario):
    """List cluster namespaces."""

    def run(self):
        """List cluster namespaces."""
        self.assertTrue(self.client.list_namespaces())

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

from rally.task import scenario

from rally_plugins.scenarios.kubernetes import common as common_scenario


@scenario.configure("Kubernetes.create_and_delete_job", platform="kubernetes")
class CreateAndDeleteJob(common_scenario.BaseKubernetesScenario):

    def run(self, image, command, image_pull_policy='IfNotPresent', name=None,
            status_wait=True):
        """Create job with no restart policy, wait for success and delete then.

        :param image: job container's image
        :param image_pull_policy: override default image pull policy
        :param command: job container's command
        :param name: job custom name
        :param status_wait: wait for success if True
        """
        namespace = self.choose_namespace()

        name = self.client.create_job(
            name,
            namespace=namespace,
            image=image,
            image_pull_policy=image_pull_policy,
            command=command,
            status_wait=status_wait
        )

        self.client.delete_job(
            name,
            namespace=namespace,
            status_wait=status_wait
        )

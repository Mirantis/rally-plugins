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


@scenario.configure(name="Kubernetes.create_and_delete_emptydir_volume",
                    platform="kubernetes")
class CreateAndDeleteEmptyDirVolume(common.KubernetesScenario):

    def run(self, image, mount_path, sleep_time, retries_total):
        """Create pod with emptyDir volume, wait it readiness and delete then.

        :param image: pod's image
        :param mount_path: path to mount volume in pod
        :param sleep_time: poll interval between each two retries
        :param retries_total: number of total retries of reading status
        """
        name = self.generate_name()
        namespace = self._choose_namespace()

        self.assertTrue(
            self.client.create_emptydir_volume_pod_and_wait_running(
                name,
                image=image,
                mount_path=mount_path,
                namespace=namespace,
                sleep_time=sleep_time,
                retries_total=retries_total
            )
        )

        self.assertTrue(self.client.delete_pod(
            name,
            namespace=namespace,
            sleep_time=sleep_time,
            retries_total=retries_total
        ))


@scenario.configure(name="Kubernetes.create_check_and_delete_emptydir_volume",
                    platform="kubernetes")
class CreateCheckDeleteEmptyDirVolume(common.KubernetesScenario):

    def run(self, image, mount_path, check_cmd, sleep_time, retries_total):
        """Create pod with emptyDir volume, wait it readiness and delete then.

        :param image: pod's image
        :param mount_path: path to mount volume in pod
        :param check_cmd: check command to exec in pod
        :param sleep_time: poll interval between each two retries
        :param retries_total: number of total retries of reading status
        """
        name = self.generate_name()
        namespace = self._choose_namespace()

        self.assertTrue(
            self.client.create_emptydir_volume_pod_and_wait_running(
                name,
                image=image,
                mount_path=mount_path,
                namespace=namespace,
                sleep_time=sleep_time,
                retries_total=retries_total
            )
        )

        self.assertTrue(self.client.check_volume_pod_existence(
            name,
            namespace=namespace,
            check_cmd=check_cmd
        ))

        self.assertTrue(self.client.delete_pod(
            name,
            namespace=namespace,
            sleep_time=sleep_time,
            retries_total=retries_total
        ))


@scenario.configure(name="Kubernetes.create_and_delete_secret_volume",
                    platform="kubernetes")
class CreateAndDeleteSecretVolume(common.KubernetesScenario):

    def run(self, image, mount_path, sleep_time, retries_total):
        """Create secret, create pod with it, wait for status and delete then.

        :param image: pod's image
        :param mount_path: path to mount volume in pod
        :param sleep_time: poll interval between each two retries
        :param retries_total: number of total retries of reading status
        """
        name = self.generate_name()
        namespace = self._choose_namespace()

        self.client.create_secret(name, namespace=namespace)

        self.assertTrue(
            self.client.create_secret_volume_pod_and_wait_running(
                name,
                image=image,
                mount_path=mount_path,
                namespace=namespace,
                sleep_time=sleep_time,
                retries_total=retries_total
            )
        )

        self.assertTrue(self.client.delete_pod(
            name,
            namespace=namespace,
            sleep_time=sleep_time,
            retries_total=retries_total
        ))


@scenario.configure(name="Kubernetes.create_check_and_delete_secret_volume",
                    platform="kubernetes")
class CreateCheckDeleteSecretVolume(common.KubernetesScenario):

    def run(self, image, mount_path, check_cmd, sleep_time, retries_total):
        """Create pod with secret volume, wait it readiness and delete then.

        :param image: pod's image
        :param mount_path: path to mount volume in pod
        :param check_cmd: check command to exec in pod
        :param sleep_time: poll interval between each two retries
        :param retries_total: number of total retries of reading status
        """
        name = self.generate_name()
        namespace = self._choose_namespace()

        self.client.create_secret(name, namespace=namespace)

        self.assertTrue(
            self.client.create_emptydir_volume_pod_and_wait_running(
                name,
                image=image,
                mount_path=mount_path,
                namespace=namespace,
                sleep_time=sleep_time,
                retries_total=retries_total
            )
        )

        self.assertTrue(self.client.check_volume_pod_existence(
            name,
            namespace=namespace,
            check_cmd=check_cmd
        ))

        self.assertTrue(self.client.delete_pod(
            name,
            namespace=namespace,
            sleep_time=sleep_time,
            retries_total=retries_total
        ))

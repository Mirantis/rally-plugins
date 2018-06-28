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

    def run(self, image, mount_path, sleep_time, retries_total, command=None):
        """Create pod with emptyDir volume, wait it readiness and delete then.

        :param image: pod's image
        :param mount_path: path to mount volume in pod
        :param sleep_time: poll interval between each two retries
        :param retries_total: number of total retries of reading status
        :param command: array of strings representing container command
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
                retries_total=retries_total,
                command=command
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

    def run(self, image, mount_path, check_cmd, sleep_time, retries_total,
            command=None):
        """Create pod with emptyDir volume, wait it readiness and delete then.

        :param image: pod's image
        :param mount_path: path to mount volume in pod
        :param check_cmd: check command to exec in pod
        :param sleep_time: poll interval between each two retries
        :param retries_total: number of total retries of reading status
        :param command: array of strings representing container command
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
                retries_total=retries_total,
                command=command
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

    def run(self, image, mount_path, sleep_time, retries_total, command=None):
        """Create secret, create pod with it, wait for status and delete then.

        :param image: pod's image
        :param mount_path: path to mount volume in pod
        :param sleep_time: poll interval between each two retries
        :param retries_total: number of total retries of reading status
        :param command: array of strings representing container command
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
                retries_total=retries_total,
                command=command
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

    def run(self, image, mount_path, check_cmd, sleep_time, retries_total,
            command=None):
        """Create pod with secret volume, wait it readiness and delete then.

        :param image: pod's image
        :param mount_path: path to mount volume in pod
        :param check_cmd: check command to exec in pod
        :param sleep_time: poll interval between each two retries
        :param retries_total: number of total retries of reading status
        :param command: array of strings representing container command
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
                retries_total=retries_total,
                command=command
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


@scenario.configure(name="Kubernetes.create_and_delete_hostpath_volume",
                    platform="kubernetes")
class CreateAndDeleteHostPathVolume(common.KubernetesScenario):

    def run(self, image, mount_path, volume_path, volume_type, sleep_time,
            retries_total, command=None):
        """Create pod with hostPath volume, wait for status and delete it then.

        :param image: pod's image
        :param mount_path: path to mount volume in pod
        :param volume_path: hostPath volume path in host
        :param volume_type: hostPath type according to Kubernetes docs
        :param sleep_time: poll interval between each two retries
        :param retries_total: number of total retries of reading status
        :param command: array of strings representing container command
        """
        name = self.generate_name()
        namespace = self._choose_namespace()

        self.assertTrue(
            self.client.create_hostpath_volume_pod_and_wait_running(
                name,
                image=image,
                mount_path=mount_path,
                volume_path=volume_path,
                volume_type=volume_type,
                namespace=namespace,
                sleep_time=sleep_time,
                retries_total=retries_total,
                command=command
            )
        )

        self.assertTrue(self.client.delete_pod(
            name,
            namespace=namespace,
            sleep_time=sleep_time,
            retries_total=retries_total
        ))


@scenario.configure(name="Kubernetes.create_check_and_delete_hostpath_volume",
                    platform="kubernetes")
class CreateCheckAndDeleteHostPathVolume(common.KubernetesScenario):

    def run(self, image, mount_path, volume_path, volume_type, check_cmd,
            sleep_time, retries_total, command=None):
        """Create pod with hostPath volume, wait for status and delete it then.

        :param image: pod's image
        :param mount_path: path to mount volume in pod
        :param volume_path: hostPath volume path in host
        :param volume_type: hostPath type according to Kubernetes docs
        :param check_cmd: check command to exec in pod
        :param sleep_time: poll interval between each two retries
        :param retries_total: number of total retries of reading status
        :param command: array of strings representing container command
        """
        name = self.generate_name()
        namespace = self._choose_namespace()

        self.assertTrue(
            self.client.create_hostpath_volume_pod_and_wait_running(
                name,
                image=image,
                mount_path=mount_path,
                volume_path=volume_path,
                volume_type=volume_type,
                namespace=namespace,
                sleep_time=sleep_time,
                retries_total=retries_total,
                command=command
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


@scenario.configure(
    name="Kubernetes.create_and_delete_local_persistent_volume",
    platform="kubernetes"
)
class CreateAndDeleteLocalPV(common.KubernetesScenario):

    def run(self, persistent_volume, persistent_volume_claim, mount_path,
            image, sleep_time, retries_total, command=None):
        name = self.generate_name()
        namespace = self._choose_namespace()
        storage_class = self.context["storageclass"]

        self.assertTrue(self.client.create_local_pv(
            name,
            storage_class=storage_class,
            size=persistent_volume["size"],
            volume_mode=persistent_volume["volume_mode"],
            local_path=persistent_volume["local_path"],
            access_modes=persistent_volume["access_modes"],
            node_affinity=persistent_volume["node_affinity"],
            sleep_time=sleep_time,
            retries_total=retries_total
        ))

        self.client.create_local_pvc(
            name,
            namespace=namespace,
            storage_class=storage_class,
            access_modes=persistent_volume_claim["access_modes"],
            size=persistent_volume_claim["size"]
        )

        self.assertTrue(self.client.create_local_pvc_pod_and_wait_running(
            name,
            namespace=namespace,
            image=image,
            mount_path=mount_path,
            command=command,
            sleep_time=sleep_time,
            retries_total=retries_total
        ))

        resp = self.client.get_local_pvc(name, namespace=namespace)
        self.assertNotEqual("Failed", resp.status.phase)
        if resp.status.phase != "Failed":
            LOG.info("Local PVC %s bound to pod" % name)

        self.assertTrue(self.client.delete_pod(
            name,
            namespace=namespace,
            sleep_time=sleep_time,
            retries_total=retries_total
        ))

        resp = self.client.get_local_pvc(name, namespace=namespace)
        self.assertNotEqual("Failed", resp.status.phase)
        if resp.status.phase != "Failed":
            LOG.info("Local PVC %s still in place" % name)

        resp = self.client.get_local_pv(name)
        self.assertNotEqual("Failed", resp.status.phase)
        if resp.status.phase != "Failed":
            LOG.info("Local PV %s still in place" % name)

        self.assertTrue(self.client.delete_local_pvc(
            name,
            namespace=namespace,
            sleep_time=sleep_time,
            retries_total=retries_total
        ))

        self.assertTrue(self.client.delete_local_pv(
            name,
            sleep_time=sleep_time,
            retries_total=retries_total
        ))


@scenario.configure(
    name="Kubernetes.create_check_and_delete_local_persistent_volume",
    platform="kubernetes"
)
class CreateCheckAndDeleteLocalPV(common.KubernetesScenario):

    def run(self, persistent_volume, persistent_volume_claim, check_cmd,
            mount_path, image, sleep_time, retries_total, command=None):
        name = self.generate_name()
        namespace = self._choose_namespace()
        storage_class = self.context["storageclass"]

        self.assertTrue(self.client.create_local_pv(
            name,
            storage_class=storage_class,
            size=persistent_volume["size"],
            volume_mode=persistent_volume["volume_mode"],
            local_path=persistent_volume["local_path"],
            access_modes=persistent_volume["access_modes"],
            node_affinity=persistent_volume["node_affinity"],
            sleep_time=sleep_time,
            retries_total=retries_total
        ))

        self.client.create_local_pvc(
            name,
            namespace=namespace,
            storage_class=storage_class,
            access_modes=persistent_volume_claim["access_modes"],
            size=persistent_volume_claim["size"]
        )

        self.assertTrue(self.client.create_local_pvc_pod_and_wait_running(
            name,
            namespace=namespace,
            image=image,
            mount_path=mount_path,
            command=command,
            sleep_time=sleep_time,
            retries_total=retries_total
        ))

        resp = self.client.get_local_pvc(name, namespace=namespace)
        self.assertNotEqual("Failed", resp.status.phase)
        if resp.status.phase != "Failed":
            LOG.info("Local PVC %s bound to pod" % name)

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

        resp = self.client.get_local_pvc(name, namespace=namespace)
        self.assertNotEqual("Failed", resp.status.phase)
        if resp.status.phase != "Failed":
            LOG.info("Local PVC %s still in place" % name)

        resp = self.client.get_local_pv(name)
        self.assertNotEqual("Failed", resp.status.phase)
        if resp.status.phase != "Failed":
            LOG.info("Local PV %s still in place" % name)

        self.assertTrue(self.client.delete_local_pvc(
            name,
            namespace=namespace,
            sleep_time=sleep_time,
            retries_total=retries_total
        ))

        self.assertTrue(self.client.delete_local_pv(
            name,
            sleep_time=sleep_time,
            retries_total=retries_total
        ))


@scenario.configure(name="Kubernetes.create_and_delete_configmap_volume",
                    platform="kubernetes")
class CreateAndDeleteConfigMapVolume(common.KubernetesScenario):

    def run(self, image, mount_path, configmap_data, sleep_time, retries_total,
            command=None, subpath=None):
        """Create pod with hostPath volume, wait for status and delete it then.

        :param image: pod's image
        :param mount_path: path to mount volume in pod
        :param configmap_data: configMap resource data
        :param subpath: subPath from configMap data to mount in pod
        :param sleep_time: poll interval between each two retries
        :param retries_total: number of total retries of reading status
        :param command: array of strings representing container command
        """
        name = self.generate_name()
        namespace = self._choose_namespace()

        self.client.create_configmap(
            name,
            namespace=namespace,
            data=configmap_data
        )

        self.assertTrue(
            self.client.create_configmap_volume_pod_and_wait_running(
                name,
                image=image,
                mount_path=mount_path,
                subpath=subpath,
                namespace=namespace,
                sleep_time=sleep_time,
                retries_total=retries_total,
                command=command
            )
        )

        self.assertTrue(self.client.delete_pod(
            name,
            namespace=namespace,
            sleep_time=sleep_time,
            retries_total=retries_total
        ))


@scenario.configure(name="Kubernetes.create_check_and_delete_configmap_volume",
                    platform="kubernetes")
class CreateCheckAndDeleteConfigMapVolume(common.KubernetesScenario):

    def run(self, image, mount_path, configmap_data, sleep_time, retries_total,
            check_cmd, command=None, subpath=None):
        """Create pod with hostPath volume, wait for status and delete it then.

        :param image: pod's image
        :param mount_path: path to mount volume in pod
        :param configmap_data: configMap resource data
        :param check_cmd: check command to exec in pod
        :param subpath: subPath from configMap data to mount in pod
        :param sleep_time: poll interval between each two retries
        :param retries_total: number of total retries of reading status
        :param command: array of strings representing container command
        """
        name = self.generate_name()
        namespace = self._choose_namespace()

        self.client.create_configmap(
            name,
            namespace=namespace,
            data=configmap_data
        )

        self.assertTrue(
            self.client.create_configmap_volume_pod_and_wait_running(
                name,
                image=image,
                mount_path=mount_path,
                subpath=subpath,
                namespace=namespace,
                sleep_time=sleep_time,
                retries_total=retries_total,
                command=command
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

        self.client.delete_configmap(name, namespace=namespace)

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
from rally.common import utils as commonutils
from rally.task import scenario

from rally_plugins.scenarios.kubernetes import common

CONF = cfg.CONF


@scenario.configure(
    "Kubernetes.create_check_and_delete_pod_with_cluster_ip_service",
    platform="kubernetes"
)
class CreateCheckAndDeletePodWithClusterIPSvc(common.BaseKubernetesScenario):

    def run(self, image, port, protocol, name=None, command=None,
            status_wait=True):
        """Create pod and clusterIP svc, check with curl job, delete then.

        :param image: pod's image
        :param port: pod's container port and svc port integer
        :param protocol: pod's container port and svc port protocol
        :param name: pod's custom name
        :param command: pod's array of strings representing command
        :param status_wait: wait for pod status if True
        """
        namespace = self.choose_namespace()
        labels = {"app": self.generate_random_name()}

        name = self.client.create_pod(
            name,
            image=image,
            namespace=namespace,
            command=command,
            port=port,
            protocol=protocol,
            labels=labels,
            status_wait=status_wait
        )

        self.client.create_service(
            name,
            namespace=namespace,
            port=port,
            protocol=protocol,
            type="ClusterIP",
            labels=labels
        )

        commonutils.interruptable_sleep(CONF.kubernetes.start_prepoll_delay)

        endpoints = self.client.get_endpoints(name, namespace=namespace)
        ips = []
        for subset in endpoints.subsets:
            addrs = [addr.ip for addr in subset.addresses]
            ports = [p.port for p in subset.ports]
            ips.extend(["%s:%s" % (a, p) for a in addrs for p in ports])

        command = ["curl"]
        command.extend(ips)
        self.client.create_job(
            name,
            namespace=namespace,
            image="appropriate/curl",
            command=command,
            status_wait=True
        )

        self.client.delete_job(
            name,
            namespace=namespace,
            status_wait=status_wait
        )
        self.client.delete_service(name, namespace=namespace)
        self.client.delete_pod(
            name,
            namespace=namespace,
            status_wait=status_wait
        )

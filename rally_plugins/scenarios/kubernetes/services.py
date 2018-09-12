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

import requests

from rally.common import cfg
from rally.common import utils as commonutils
from rally import exceptions
from rally.task import atomic
from rally.task import scenario

from rally_plugins.scenarios.kubernetes import common as common_scenario

CONF = cfg.CONF


@scenario.configure(
    "Kubernetes.create_check_and_delete_pod_with_cluster_ip_service",
    platform="kubernetes"
)
class PodWithClusterIPSvc(common_scenario.BaseKubernetesScenario):

    def run(self, image, port, protocol, command=None, status_wait=True):
        """Create pod and clusterIP svc, check with curl job, delete then.

        :param image: pod's image
        :param port: pod's container port and svc port integer
        :param protocol: pod's container port and svc port protocol
        :param command: pod's array of strings representing command
        :param status_wait: wait for pod status if True
        """
        namespace = self.choose_namespace()
        labels = {"app": self.generate_random_name()}

        name = self.client.create_pod(
            image,
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


@scenario.configure(
    "Kubernetes.create_check_and_delete_pod_with_cluster_ip_service_"
    "custom_endpoints",
    platform="kubernetes"
)
class PodWithClusterIPSvcWithEndpoints(common_scenario.BaseKubernetesScenario):

    def run(self, image, port, protocol, command=None, status_wait=True):
        """Create pod and clusterIP svc with custom endpoints.

        Create pod and clusterIP svc with custom endpoints, check it with curl
        job and delete them all then.

        :param image: pod's image
        :param port: pod's container port and svc port integer
        :param protocol: pod's container port and svc port protocol
        :param command: pod's array of strings representing command
        :param status_wait: wait for pod status if True
        """
        namespace = self.choose_namespace()

        name = self.client.create_pod(
            image,
            namespace=namespace,
            command=command,
            port=port,
            protocol=protocol,
            status_wait=status_wait
        )

        self.client.create_service(
            name,
            namespace=namespace,
            port=port,
            protocol=protocol,
            type="ClusterIP"
        )

        ip = self.client.get_pod(name, namespace=namespace).status.pod_ip

        self.client.create_endpoints(
            name,
            namespace=namespace,
            ip=ip,
            port=port
        )

        command = ["curl", "%s:%s" % (ip, port)]
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
        self.client.delete_endpoints(name, namespace=namespace)
        self.client.delete_service(name, namespace=namespace)
        self.client.delete_pod(
            name,
            namespace=namespace,
            status_wait=status_wait
        )


@scenario.configure(
    "Kubernetes.create_check_and_delete_pod_with_node_port_service",
    platform="kubernetes"
)
class PodWithNodePortService(common_scenario.BaseKubernetesScenario):

    def run(self, image, port, protocol, request_timeout=None,
            command=None, status_wait=True):
        """Create pod and nodePort svc, request pod by port and delete then.

        :param image: pod's image
        :param port: pod's container port and svc port integer
        :param protocol: pod's container port and svc port protocol
        :param request_timeout: GET request timeout for check nodePort svc IP
        :param command: pod's array of strings representing command
        :param status_wait: wait for pod status if True
        """
        namespace = self.choose_namespace()
        labels = {"app": self.generate_random_name()}

        name = self.client.create_pod(
            image,
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
            type="NodePort",
            labels=labels
        )

        svc = self.client.get_service(name, namespace=namespace)

        node_port = svc.spec.ports[0].node_port

        commonutils.interruptable_sleep(CONF.kubernetes.start_prepoll_delay)

        with atomic.ActionTimer(self, "kubernetes.request_node_port_service"):
            server = self.context["env"]["platforms"]["kubernetes"]["server"]

            sleep_time = CONF.kubernetes.status_poll_interval
            retries_total = CONF.kubernetes.status_total_retries

            i = 0
            if server.startswith("http"):
                ip = "://" + server[server.index(":"):server.rindex(":") + 1]
            else:
                ip = server[:server.index(":")]
            url = ("http" + ip + str(node_port) + "/")
            while i < retries_total:
                try:
                    kwargs = {}
                    if request_timeout:
                        kwargs["timeout"] = request_timeout
                    requests.get(url, **kwargs)
                except (requests.ConnectionError, requests.ReadTimeout) as ex:
                    if i < retries_total:
                        i += 1
                        commonutils.interruptable_sleep(sleep_time)
                    else:
                        raise exceptions.RallyException(
                            message="Unable to get response "
                                    "from %(url)s: %(ex)s" % {
                                        "url": url,
                                        "ex": str(ex)
                                    })
                else:
                    break

        self.client.delete_service(name, namespace=namespace)
        self.client.delete_pod(
            name,
            namespace=namespace,
            status_wait=status_wait
        )
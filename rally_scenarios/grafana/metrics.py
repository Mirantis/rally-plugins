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
from rally.common import logging
from rally.common import utils as commonutils
from rally.task import scenario as commonscenario
from rally.task import types
from rally.task import utils
from rally.task import validation

from rally_openstack import consts
from rally_openstack import scenario

CONF = cfg.CONF
LOG = logging.getLogger(__name__)

"""Scenarios for Pushgateway and Grafana metrics."""


class PushMetricBasic(commonscenario.Scenario):
    """Utility method for push metric scenarios."""

    def _check_metric(self, seed, monitor_vip, grafana, datasource_id,
                      sleep_time, retries_total):
        check_url = ("http://%(vip)s:%(port)s/api/datasources/proxy/:"
                     "%(datasource)s/api/v1/query?"
                     "query=rally_test_metric_%(seed)s" % {
                         "vip": monitor_vip,
                         "port": grafana["port"],
                         "datasource": datasource_id,
                         "seed": seed
                     })
        i = 0
        LOG.info("Check metric rally_test_metric_%s in Grafana" % seed)
        while i < retries_total:
            LOG.info("Attempt number %s" % (i + 1))
            resp = requests.get(check_url,
                                auth=(grafana["user"], grafana["password"]))
            result = resp.json()
            LOG.info("Grafana response code: %s" % resp.status_code)
            if len(result["data"]["result"]) < 1 and i + 1 >= retries_total:
                LOG.warning("No instance metrics found in Grafana")
                self.assertGreater(len(result["data"]["result"]), 0)
            elif len(result["data"]["result"]) < 1:
                i += 1
                commonutils.interruptable_sleep(sleep_time)
            else:
                LOG.warning("Metric instance found in Grafana")
                self.assertGreater(len(result["data"]["result"]), 0)
                break


@types.convert(image={"type": "glance_image"},
               flavor={"type": "nova_flavor"})
@validation.add("required_services", services=[consts.Service.NOVA])
@validation.add("required_platform", platform="openstack", admin=True)
@scenario.configure(context={"cleanup@openstack": ["nova"]},
                    name="GrafanaMetrics.push_metric_from_instance",
                    platform="openstack")
class PushMetricsInstance(PushMetricBasic, scenario.OpenStackScenario):
    """Test monitoring system by pushing metric from nova server and check it.

    Scenario tests monitoring system, which uses Pushgateway as metric exporter
    and Grafana as metrics monitoring.

    The goal of the test is to check that monitoring system works correctly
    with nova instance. Test case is the following: we deploy some env with
    nodes on Openstack nova instances, add metric exporter (using Pushgateway
    in this test) inside nodes (i.e. nova instances) for some interested
    metrics (e.g. CPU, memory etc.). We want to check that metrics successfully
    sends to metrics storage (e.g. Prometheus) by requesting Grafana. Create
    nova instance, add Pushgateway push random metric to userdata and after
    instance would be available, check Grafana datasource that pushed metric in
    data.
    """

    def _push_metric(self, seed, image, flavor, monitor_vip, pushgateway_port):
        push_cmd = (
            "echo rally_test_metric_%(seed)s 12345 | curl --data-binary "
            "@- http://%(monitor_vip)s:%(pgtw_port)s/metrics/job"
            "/rally_test" % {"seed": seed,
                             "monitor_vip": monitor_vip,
                             "pgtw_port": pushgateway_port})
        userdata = ("#!/bin/bash\n%s" % push_cmd)
        server = self.clients("nova").servers.create(seed,
                                                     image, flavor,
                                                     userdata=userdata)
        LOG.info("Server %s create started" % seed)
        self.sleep_between(CONF.openstack.nova_server_boot_prepoll_delay)
        utils.wait_for_status(
            server,
            ready_statuses=["ACTIVE"],
            update_resource=utils.get_from_manager(),
            timeout=CONF.openstack.nova_server_boot_timeout,
            check_interval=CONF.openstack.nova_server_boot_poll_interval
        )
        LOG.info("Server %s with pushing metric script (metric exporter) is "
                 "active" % seed)

    def run(self, image, flavor, monitor_vip, pushgateway_port,
            grafana, datasource_id, sleep_time=5, retries_total=30):
        """Create nova instance with pushing metric script as userdata.

        Push metric to metrics storage using Pushgateway and check it in
        Grafana.

        :param image: image for server with userdata script
        :param flavor: flavor for server with userdata script
        :param monitor_vip: monitoring system IP to push metric
        :param pushgateway_port: Pushgateway port to use for pushing metric
        :param grafana: Grafana dict with creds and port to use for checking
               metric. Format: {user: admin, password: pass, port: 9902}
        :param datasource_id: metrics storage datasource ID in Grafana
        :param sleep_time: sleep time between checking metrics in seconds
        :param retries_total: total number of retries to check metric in
                              Grafana
        """
        seed = self.generate_random_name()

        self._push_metric(seed, image, flavor, monitor_vip, pushgateway_port)
        self._check_metric(seed, monitor_vip, grafana, datasource_id,
                           sleep_time, retries_total)


@scenario.configure(name="GrafanaMetrics.push_metric_locally")
class PushMetricLocal(PushMetricBasic, commonscenario.Scenario):
    """Test monitoring system availability with local pushing random metric."""

    def run(self, monitor_vip, pushgateway_port, grafana, datasource_id,
            sleep_time=5, retries_total=30):
        """Push random metric to Pushgateway locally and check it in Grafana.

        :param monitor_vip: monitoring system IP to push metric
        :param pushgateway_port: Pushgateway port to use for pushing metric
        :param grafana: Grafana dict with creds and port to use for checking
               metric. Format: {user: admin, password: pass, port: 9902}
        :param datasource_id: metrics storage datasource ID in Grafana
        :param sleep_time: sleep time between checking metrics in seconds
        :param retries_total: total number of retries to check metric in
                              Grafana
        """
        seed = self.generate_random_name()

        push_url = "http://%(ip)s:%(port)s/metrics/job/rally_test" % {
            "ip": monitor_vip,
            "port": pushgateway_port
        }
        resp = requests.post(push_url,
                             headers={"Content-type": "text/xml"},
                             data="rally_test_metric_%s 12345\n" % seed)
        if resp.ok:
            LOG.info("Metric %s pushed locally")
        else:
            LOG.error("Error during push metric %s")
            self.assertFalse(resp.ok)
        self._check_metric(seed, monitor_vip, grafana, datasource_id,
                           sleep_time, retries_total)

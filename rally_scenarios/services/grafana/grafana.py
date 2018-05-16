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

from rally.common import logging
from rally.common import utils as commonutils
from rally.task import atomic
from rally.task import service

LOG = logging.getLogger(__name__)


class GrafanaService(service.Service):

    @atomic.action_timer("grafana.push_metric")
    def push_metric(self, seed, monitor_vip, pushgateway_port, job_name):
        """Push metric by GET request using pushgateway.

        :param seed: random name for metric to push
        :param monitor_vip: monitoring system IP to push metric
        :param pushgateway_port: Pushgateway port to use for pushing metric
        :param job_name: job name to push metric in it
        """
        push_url = "http://%(ip)s:%(port)s/metrics/job/%(job)s" % {
            "ip": monitor_vip,
            "port": pushgateway_port,
            "job": job_name
        }
        resp = requests.post(push_url,
                             headers={"Content-type": "text/xml"},
                             data="%s 12345\n" % seed)
        if resp.ok:
            LOG.info("Metric %s pushed" % seed)
        else:
            LOG.error("Error during push metric %s" % seed)
        return resp.ok

    @atomic.action_timer("grafana.check_metric")
    def check_metric(self, seed, monitor_vip, grafana, datasource_id,
                     sleep_time, retries_total):
        """Check metric with seed name in Grafana datasource.

        :param seed: random metric name
        :param monitor_vip: monitoring system IP to push metric
        :param grafana: Grafana dict with creds and port to use for checking
               metric. Format: {user: admin, password: pass, port: 9902}
        :param datasource_id: metrics storage datasource ID in Grafana
        :param sleep_time: sleep time between checking metrics in seconds
        :param retries_total: total number of retries to check metric in
                              Grafana
        :return: True if metric in Grafana datasource and False otherwise
        """
        check_url = ("http://%(vip)s:%(port)s/api/datasources/proxy/:"
                     "%(datasource)s/api/v1/query?query=%(seed)s" % {
                         "vip": monitor_vip,
                         "port": grafana["port"],
                         "datasource": datasource_id,
                         "seed": seed
                     })
        i = 0
        LOG.info("Check metric %s in Grafana" % seed)
        while i < retries_total:
            LOG.debug("Attempt number %s" % (i + 1))
            resp = requests.get(check_url,
                                auth=(grafana["user"], grafana["password"]))
            result = resp.json()
            LOG.debug("Grafana response code: %s" % resp.status_code)
            if len(result["data"]["result"]) < 1 and i + 1 >= retries_total:
                LOG.debug("No instance metrics found in Grafana")
                return False
            elif len(result["data"]["result"]) < 1:
                i += 1
                commonutils.interruptable_sleep(sleep_time)
            else:
                LOG.debug("Metric instance found in Grafana")
                return True

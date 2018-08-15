# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import rally_openstack
from rally_openstack import scenario


class configure(object):
    def __init__(self, **kwargs):
        self.dec_kwargs = kwargs

    def __call__(self, cls):
        if rally_openstack.__rally_version__ < (1, 0):
            return scenario.configure(**self.dec_kwargs)(cls)
        return cls

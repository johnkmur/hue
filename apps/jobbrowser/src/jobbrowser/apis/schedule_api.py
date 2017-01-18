#!/usr/bin/env python
# Licensed to Cloudera, Inc. under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  Cloudera, Inc. licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import json

from django.utils.translation import ugettext as _

from liboozie.oozie_api import get_oozie

from jobbrowser.apis.base_api import Api, MockDjangoRequest
from liboozie.utils import format_time
from oozie.views.dashboard import get_oozie_job_log


LOG = logging.getLogger(__name__)


try:
  from oozie.conf import OOZIE_JOBS_COUNT
  from oozie.views.dashboard import list_oozie_coordinator
except Exception, e:
  LOG.exception('Some application are not enabled: %s' % e)


class ScheduleApi(Api):

  def apps(self):
    oozie_api = get_oozie(self.user)
    kwargs = {'cnt': OOZIE_JOBS_COUNT.get(), 'filters': []}
    wf_list = oozie_api.get_coordinators(**kwargs)

    return [{
        'id': app.id,
        'name': app.appName,
        'status': app.status,
        'type': 'schedule',
        'user': app.user,
        'progress': 100,
        'duration': 10 * 3600,
        'submitted': 10 * 3600
    } for app in wf_list.jobs]


  def app(self, appid):
    oozie_api = get_oozie(self.user)
    coordinator = oozie_api.get_coordinator(jobid=appid)

    request = MockDjangoRequest(self.user, get=MockGet())
    response = list_oozie_coordinator(request, job_id=appid)

    common = {
        'id': coordinator.coordJobId,
        'name': coordinator.coordJobName,
        'status': coordinator.status,
        'type': 'schedule',
        'startTime': format_time(coordinator.startTime),
    }
    common['properties'] = json.loads(response.content)
    common['properties']['xml'] = ''
    common['properties']['properties'] = ''

    return common

  def logs(self, appid, app_type):
    request = MockDjangoRequest(self.user)
    data = get_oozie_job_log(request, job_id=appid)

    return {'progress': 0, 'logs': {'default': json.loads(data.content)['log']}}


  def profile(self, appid, app_type, app_property):
    if app_property == 'xml':
      oozie_api = get_oozie(self.user)
      workflow = oozie_api.get_coordinator(jobid=appid)
      return {
        'xml': workflow.definition,
      }
    elif app_property == 'properties':
      oozie_api = get_oozie(self.user)
      workflow = oozie_api.get_coordinator(jobid=appid)
      return {
        'properties': workflow.conf_dict,
      }



class MockGet():
  def __ini__(self, statuses):
    self.statuses = []

  def get(self, prop, default=None):
    if prop == 'format':
      return 'json'
    else:
      return default

  def getlist(self, prop):
    return []

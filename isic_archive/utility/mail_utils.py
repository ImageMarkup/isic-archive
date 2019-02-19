#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#  Copyright Kitware Inc.
#
#  Licensed under the Apache License, Version 2.0 ( the "License" );
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
###############################################################################
from email.mime.text import MIMEText

import six

from girder import logger
from girder.constants import SettingKey
from girder.models.group import Group
from girder.models.setting import Setting
from girder.utility import mail_utils


def sendEmail(to, subject, text):
    if isinstance(to, six.string_types):
        to = (to,)

    if isinstance(text, six.text_type):
        text = text.encode('utf8')

    msg = MIMEText(text, 'html', 'UTF-8')
    msg['Subject'] = subject or '[no subject]'
    msg['To'] = ', '.join(to)
    msg['From'] = Setting().get(SettingKey.EMAIL_FROM_ADDRESS)
    recipients = list(set(to))
    smtp = mail_utils._SMTPConnection(
        host=Setting().get(SettingKey.SMTP_HOST, 'localhost'),
        port=Setting().get(SettingKey.SMTP_PORT, None),
        encryption=Setting().get(SettingKey.SMTP_ENCRYPTION, 'none'),
        username=Setting().get(SettingKey.SMTP_USERNAME, None),
        password=Setting().get(SettingKey.SMTP_PASSWORD, None)
    )

    logger.info('Sending email to %s through %s', ', '.join(recipients), smtp.host)

    with smtp:
        smtp.send(msg['From'], recipients, msg.as_string())


def sendEmailToGroup(groupName, templateFilename, templateParams, subject=None):
    """
    Send a single email with all members of a group as the recipients.

    :param groupName: The name of the group.
    :param templateFilename: The name of the Make template file used to format
        the email.
    :param templateParams: The parameters with which to render the template.
    :param subject: The subject line of the email.
    """
    group = Group().findOne({'name': groupName})
    if not group:
        raise Exception('Could not load group: %s.' % groupName)
    emails = [member['email'] for member in Group().listMembers(group)]
    if emails:
        html = mail_utils.renderTemplate(templateFilename, templateParams)
        sendEmail(to=emails, subject=subject, text=html)

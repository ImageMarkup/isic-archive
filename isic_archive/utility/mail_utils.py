from email.mime.text import MIMEText

from girder import logger
from girder.models.group import Group
from girder.models.setting import Setting
from girder.settings import SettingKey
from girder.utility import mail_utils


def sendEmail(to, subject, text):
    if isinstance(to, str):
        to = (to,)

    msg = MIMEText(text, 'html')
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
        raise Exception(f'Could not load group: {groupName}.')
    emails = [member['email'] for member in Group().listMembers(group)]
    if emails:
        html = mail_utils.renderTemplate(templateFilename, templateParams)
        sendEmail(to=emails, subject=subject, text=html)

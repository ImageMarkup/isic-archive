from girder.models.group import Group
from girder.utility import mail_utils


def sendEmailToGroup(groupName, templateFilename, templateParams, subject=None, asynchronous=True):
    """
    Send a single email with all members of a group as the recipients.

    :param groupName: The name of the group.
    :param templateFilename: The name of the Make template file used to format
        the email.
    :param templateParams: The parameters with which to render the template.
    :param subject: The subject line of the email.
    :param asynchronous: If False, bypass Girder's event system.
    """
    group = Group().findOne({'name': groupName})
    if not group:
        raise Exception(f'Could not load group: {groupName}.')
    emails = [member['email'] for member in Group().listMembers(group)]
    if emails:
        html = mail_utils.renderTemplate(templateFilename, templateParams)
        if asynchronous:
            mail_utils.sendMail(subject, html, emails)
        else:
            mail_utils.sendMailSync(subject, html, emails)

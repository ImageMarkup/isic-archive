import os

from celery import Celery, Task
from celery.signals import worker_process_init
import jsonpickle
from kombu.serialization import register
import pkg_resources
from requests_toolbelt.sessions import BaseUrlSession

from girder.constants import SettingKey, TokenScope
from girder.models.setting import Setting
from girder.models.token import Token
from girder.utility import mail_utils

from isic_archive.provision_utility import getAdminUser


class CredentialedGirderTask(Task):
    """
    Provide a task with a requests session via self.session, this is the default task.

    This base task should always be used in conjunction with setting bind=True in order
    to access the session.
    """

    def __call__(self, *args, **kwargs):
        """
        Create a token and configure a requests session object with it.

        The child class overrides run, so __call__ must be used to hook in before a task
        is executed.
        """
        # TODO: Revoke token in post task signal
        self.token = Token().createToken(user=getAdminUser(), days=1,
                                         scope=[TokenScope.DATA_READ, TokenScope.DATA_WRITE])
        self.session = BaseUrlSession(
            os.getenv(
                'ARCHIVE_API_URL',
                Setting().get(SettingKey.SERVER_ROOT)
            ).rstrip('/') + '/')
        self.session.headers.update({
            'Girder-Token': str(self.token['_id'])
        })

        super(CredentialedGirderTask, self).__call__(*args, **kwargs)


app = Celery(task_cls=CredentialedGirderTask)


class CeleryAppConfig(object):
    # jsonpickle is used to support passing object ids between tasks
    task_serializer = 'jsonpickle'

    # TODO: Remove when Celery version >= 4.3 since it then infers from env vars
    result_backend = os.getenv('CELERY_RESULT_BACKEND')


app.config_from_object(CeleryAppConfig())


@app.on_after_configure.connect
def setupPeriodicTasks(sender, **kwargs):
    from isic_archive_tasks.notification import maybeSendIngestionNotifications
    sender.add_periodic_task(30, maybeSendIngestionNotifications.s(),
                             name='Send any necessary notifications for ingested batches.')


@worker_process_init.connect
def addMailTemplates(sender, **kwargs):
    mail_utils.addTemplateDirectory(
        pkg_resources.resource_filename('isic_archive', 'mail_templates'),
        prepend=True)


register('jsonpickle', jsonpickle.encode, jsonpickle.decode, content_type='application/json',
         content_encoding='utf-8')

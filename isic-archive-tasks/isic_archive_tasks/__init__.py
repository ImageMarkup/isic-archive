import os

from celery import Celery, Task
from celery.signals import worker_process_init
from celery.utils.log import get_task_logger
import jsonpickle
from girder.models.setting import Setting
from kombu.serialization import register
import sentry_sdk

from girder.constants import TokenScope, SettingKey
from girder.models.token import Token
from requests_toolbelt.sessions import BaseUrlSession


class CredentialedGirderTask(Task):
    """
    Provide a task with a requests session via self.session, this is the default task.

    This base task should always be used in conjunction with setting bind=True in order
    to access the session.
    """
    def __call__(self, *args, **kwargs):
        """
        The child class overrides run, so __call__ must be used to hook in before a task
        is executed.
        """
        from girder.plugins.isic_archive.provision_utility import getAdminUser
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


app = Celery(broker='redis://localhost', backend='redis://localhost',
             task_cls=CredentialedGirderTask)


class CeleryAppConfig(object):
    # jsonpickle is used to support passing object ids between tasks
    task_serializer = 'jsonpickle'


app.config_from_object(CeleryAppConfig())

task_logger = get_task_logger(__name__)
sentry_sdk.init()


@app.on_after_configure.connect
def setupPeriodicTasks(sender, **kwargs):
    sender.add_periodic_task(30, maybeSendIngestionNotifications.s(),
                             name='Send any necessary notifications for ingested batches.')


@worker_process_init.connect
def fixGirderImports(sender, **kwargs):
    from girder.utility.server import configureServer
    configureServer(curConfig={
        'server': {
            'mode': 'production'
        },
        'cherrypy_server': False
    })


register('jsonpickle', jsonpickle.encode, jsonpickle.decode, content_type='application/json',
         content_encoding='utf-8')


from .image import ingestImage, markImageIngested, generateSuperpixels, generateLargeImage
from .notification import maybeSendIngestionNotifications, sendIngestionNotification
from .zip import ingestBatchFromZipfile

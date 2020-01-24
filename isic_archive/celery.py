from celery import Celery, Task
from celery.signals import worker_process_init
import jsonpickle
from kombu.serialization import register
import pkg_resources
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from requests_toolbelt.sessions import BaseUrlSession
import sentry_sdk

from girder.constants import TokenScope
from girder.models.token import Token
from girder.utility import mail_utils

from isic_archive import settings
from isic_archive.provision_utility import getAdminUser

sentry_sdk.init()


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
        self.session = BaseUrlSession(settings.ISIC_API_URL)
        self.session.headers.update({
            'Girder-Token': str(self.token['_id'])
        })

        retry = Retry(total=10, read=10, connect=10, backoff_factor=.2,
                      method_whitelist=False, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)  #
        super(CredentialedGirderTask, self).__call__(*args, **kwargs)


class CeleryAppConfig(object):
    # jsonpickle is used to support passing object ids between tasks
    task_serializer = 'jsonpickle'
    worker_concurrency = 1
    task_ignore_result = True
    task_time_limit = 7200
    # Necessary for task monitoring with Flower
    worker_sent_task_events = True
    # Prefetching is only necessary with high-latency brokers, and apparently can cause problems
    worker_prefetch_multiplier = 1


app = Celery(task_cls=CredentialedGirderTask, config_source=CeleryAppConfig)


@app.on_after_configure.connect
def setupPeriodicTasks(sender, **kwargs):
    from isic_archive.tasks import maybeSendIngestionNotifications
    sender.add_periodic_task(30, maybeSendIngestionNotifications.s(),
                             name='Send any necessary notifications for ingested batches.')


@worker_process_init.connect
def addMailTemplates(sender, **kwargs):
    """Perform the necessary steps from IsicArchive.load."""
    mail_utils.addTemplateDirectory(
        pkg_resources.resource_filename('isic_archive', 'mail_templates'),
        prepend=True)


register('jsonpickle', jsonpickle.encode, jsonpickle.decode, content_type='application/json',
         content_encoding='utf-8')

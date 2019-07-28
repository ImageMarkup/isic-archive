import cherrypy

from girder.api import access

from .base import IsicResource


class RedirectsResource(IsicResource):
    def __init__(self):
        super(RedirectsResource, self).__init__()
        self.resourceName = 'redirects'

        self.route('GET', ('uploadBatch',), self.redirectUploadBatch)
        self.route('GET', ('literature',), self.redirectLiterature)
        self.route('GET', ('registerMetadata',), self.redirectRegisterMetadata)
        self.route('GET', ('applyMetadata',), self.redirectApplyMetadata)

    def _doRedirect(self, url):
        exc = cherrypy.HTTPRedirect(url, status=307)
        # "cherrypy.HTTPRedirect" will convert all URLs to be absolute and
        # external; however, the hostname for external URLs may not be deduced
        # correctly in all environments, so keep the url as-is
        exc.urls = [url]
        raise exc

    @access.public
    def redirectUploadBatch(self, params):
        self._doRedirect('/#dataset/upload/batch')

    @access.public
    def redirectLiterature(self, params):
        self._doRedirect('/#literature')

    @access.public
    def redirectRegisterMetadata(self, params):
        self._doRedirect(f'/#dataset/{str(params.get("datasetId", ""))}/metadata/register')

    @access.public
    def redirectApplyMetadata(self, params):
        self._doRedirect(f'/#dataset/{str(params.get("datasetId", ""))}/metadata/apply')

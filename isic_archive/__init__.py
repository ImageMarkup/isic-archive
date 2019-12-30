import pkg_resources
import sentry_sdk

from girder import events
from girder.api.v1 import resource
from girder.plugin import getPlugin, GirderPlugin
from girder.utility import mail_utils
from girder.utility.model_importer import ModelImporter

from isic_archive.models import Annotation, Batch, Dataset, Image, Segmentation, Study, User
from . import api
# Import settings for side effects
from . import settings  # noqa: F401
from .provision_utility import provisionDatabase


def onDescribeResource(event):
    # Patch a bug with how Girder's Swagger descriptions work with Vagrant
    # port forwarding and Nginx proxies
    # This is fundamentally a problem with "rest.getApiUrl"
    describeResponse = event.info['returnVal']
    # TODO: get this from the server config or the request
    describeResponse['basePath'] = '/api/v1'


def onUserCreate(event):
    newUser = event.info

    # If there are no other users, besides the Archive admin
    if not User().collection.count_documents({
        'email': {'$nin': [
            'admin@isic-archive.com',
            # The new user has already been saved, when 'model.user.save.created' is triggered
            newUser['email'],
        ]}
    }):
        # Make this user an admin
        newUser['admin'] = True
        User().update(
            {'_id': newUser['_id']},
            {'$set': {'admin': True}},
            multi=False
        )


def clearRouteDocs():
    from girder.api.docs import routes

    # Preserve some upstream operations for user lifecycle management
    savedRoutes = {}
    for routeMethod, routePath in {
        ('GET', '/user/authentication'),  # log in by password
        ('DELETE', '/user/authentication'),  # log out
        ('GET', '/user/me'),  # personal info on the current user
        ('POST', '/user'),  # personal info on the current user
        ('GET', '/oauth/provider'),  # initiate an OAuth2 workflow for login / registration
        ('PUT', '/user/{id}'),  # change personal info
        ('PUT', '/user/password'),  # change password
        ('PUT', '/user/password/temporary'),  # initiate email reset of forgotten password
        ('GET', '/user/password/temporary/{id}'),  # complete email reset of forgotten password
        ('POST', '/user/verification'),  # resend an email verification message
    }:
        # The [0] element of the routePath split is '', since it starts with a '/'
        routeResource = routePath.split('/')[1]
        try:
            routeOperation = routes[routeResource][routePath][routeMethod]
        except KeyError:
            continue
        savedRoutes[(routeResource, routePath, routeMethod)] = routeOperation

    routes.clear()

    for (routeResource, routePath, routeMethod), routeOperation in savedRoutes.items():
        routes[routeResource][routePath][routeMethod] = routeOperation


class IsicArchive(GirderPlugin):
    DISPLAY_NAME = 'ISIC Archive'

    def load(self, info):
        sentry_sdk.init()

        getPlugin('large_image').load(info)
        oauth = getPlugin('oauth')
        if oauth:
            oauth.load(info)
        isic_discourse_sso = getPlugin('isic_discourse_sso')
        if isic_discourse_sso:
            # If this plugin is enabled, ensure it loads first, so its API docs are cleared
            isic_discourse_sso.load(info)

        # set the title of the HTML pages
        info['serverRoot'].updateHtmlVars({'title': 'ISIC Archive'})

        # register models
        ModelImporter.registerModel('annotation', Annotation, 'isic_archive')
        ModelImporter.registerModel('batch', Batch, 'isic_archive')
        ModelImporter.registerModel('dataset', Dataset, 'isic_archive')
        ModelImporter.registerModel('image', Image, 'isic_archive')
        ModelImporter.registerModel('segmentation', Segmentation, 'isic_archive')
        ModelImporter.registerModel('study', Study, 'isic_archive')
        ModelImporter.registerModel('user', User, 'isic_archive')

        # add event listeners
        events.bind('rest.get.describe/:resource.after',
                    'isic.onDescribeResource', onDescribeResource)
        events.bind('model.user.save.created',
                    'isic.onUserCreate', onUserCreate)

        # add custom model searching
        resource.allowedSearchTypes.update({
            'image.isic_archive',
            'study.isic_archive',
        })

        # register license and mail templates
        mail_utils.addTemplateDirectory(
            pkg_resources.resource_filename('isic_archive', 'license_templates'),
            prepend=True)
        mail_utils.addTemplateDirectory(
            pkg_resources.resource_filename('isic_archive', 'mail_templates'),
            prepend=True)

        # create all necessary users, groups, collections, etc
        provisionDatabase()

        # add api routes
        # remove docs for default Girder API, to simplify page
        clearRouteDocs()

        # Customize API docs template
        baseTemplateFilename = info['apiRoot'].templateFilename
        info['apiRoot'].updateHtmlVars({
            'baseTemplateFilename': baseTemplateFilename
        })
        templatePath = pkg_resources.resource_filename('isic_archive', 'isic_api_docs.mako')
        info['apiRoot'].setTemplatePath(templatePath)

        # TODO: nest these under a "/isic" path?
        info['apiRoot'].annotation = api.AnnotationResource()
        info['apiRoot'].dataset = api.DatasetResource()
        info['apiRoot'].image = api.ImageResource()
        info['apiRoot'].redirects = api.RedirectsResource()
        info['apiRoot'].segmentation = api.SegmentationResource()
        info['apiRoot'].study = api.StudyResource()
        info['apiRoot'].task = api.TaskResource()
        api.attachUserApi(info['apiRoot'].user)

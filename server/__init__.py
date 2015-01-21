
import functools
import os

from girder import events
from provision_utility import initialSetup
from gallery import GalleryHandler
from upload import uploadHandler
from image_utility import zoomifyhandler, thumbnailhandler, fifHandler, annotationHandler, segmentationSourceHandler, segmentationTileHandler
from qc import QCHandler
from task_utility import tasklisthandler, TaskHandler, UDAResource

from annotate import AnnotateHandler, FillHandler, MapHandler

def public_access(fun):
    @functools.wraps(fun)
    def accessDecorator(*args, **kwargs):
        return fun(*args, **kwargs)
    accessDecorator.accessLevel = 'public'
    return accessDecorator


def load(info):


    # create all necessary users, groups, collections, etc
    initialSetup()


    # add static file serving

    app_base = os.path.join(os.curdir, os.pardir)
    app_path = os.path.join(app_base, 'girder', 'plugins', 'uda', 'custom')

    info['config']['/uda'] = {
        'tools.staticdir.on': 'True',
        'tools.staticdir.dir': app_path
    }


    # add dynamic root routes
    # root endpoints -> where a user may go and expect a UI

    class Root(object):
        pass

    uda_root = Root()


    info['apiRoot'].uda = UDAResource()

    #   uda/gallery/:folderId -> returns a single page gallery

    uda_root.gallery = GalleryHandler()



    #   uda/qc/:folderId -> returns a QC page where user can move images to

    uda_root.qc = QCHandler()



    #   uda/view/:itemId -> simple zoomable viewer for an image

    # TODO



    #   uda/task/:userId -> redirects to appropriate task view for the user

    uda_root.task = TaskHandler()



    #   uda/annotator -> the reconfigurable image annotator

    uda_root.annotate = AnnotateHandler()

    uda_root.map = MapHandler()

    uda_root.fill = FillHandler()


    # add route to root route '/'

    info['serverRoot'].uda = uda_root





    # add api routes

    # item/:id/thumbnail -> returns a thumbnail of the image

    info['apiRoot'].item.route('GET', (':id', 'thumbnail'), public_access(thumbnailhandler))

    # item/:id/annotation -> returns the json annotation

    info['apiRoot'].item.route('GET', (':id', 'annotation'), public_access(annotationHandler))


    # item/:id/annotation -> returns the png segmentation (index map as alpha channel)

    info['apiRoot'].item.route('GET', (':id', 'segmentationSource'), public_access(segmentationSourceHandler))

    info['apiRoot'].item.route('GET', (':id', 'segmentationTiles'), public_access(segmentationTileHandler))


    # item/:id/zoomify -> returns a zoomify xml if available

    info['apiRoot'].item.route('GET', (':id', 'zoomify', ':p1'), public_access(zoomifyhandler))
    info['apiRoot'].item.route('GET', (':id', 'zoomify', ':p1', ':p2'), public_access(zoomifyhandler))


    # item/:id/fif -> returns the IIP FIF endpoint for an item

    info['apiRoot'].item.route('GET', (':id', 'fif', ':fifparams'), public_access(fifHandler))

    # user/:userId/tasklist -> returns a list of images and any UI configuration

    info['apiRoot'].user.route('GET', (':id', 'tasklist'), public_access(tasklisthandler))

    # add event listeners

    events.bind('data.process', 'uploadHandler', public_access(uploadHandler))




    # add the base directory to serve

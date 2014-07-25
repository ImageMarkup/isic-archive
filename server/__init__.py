
import os

from girder import events
from provision_utility import initialSetup
from gallery import GalleryHandler
from upload import uploadHandler
from image_utility import zoomifyhandler, thumbnailhandler
from qc import QCHandler
from task_utility import tasklisthandler, taskCompleteHandler, TaskHandler




def load(info):


    # create all necessary users, groups, collections, etc

    initialSetup()


    # add static file serving

    app_base = os.path.join(os.curdir, os.pardir)
    app_path = os.path.join(app_base, 'udaapp')

    info['config']['/uda'] = {
        'tools.staticdir.on': 'True',
        'tools.staticdir.dir': app_path
    }


    # add dynamic root routes
    # root endpoints -> where a user may go and expect a UI

    class Root(object):
        pass

    uda_root = Root()

    # 	uda/gallery/:folderId -> returns a single page gallery

    uda_root.gallery = GalleryHandler()

    # 	uda/qc/:folderId -> returns a QC page where user can move images to

    uda_root.qc = QCHandler()

    # 	uda/view/:itemId -> simple zoomable viewer for an image
    #
    # 	uda/task/:userId -> redirects to appropriate task view for the user

    uda_root.task = TaskHandler()


    #
    # 	uda/annotator ->

    info['serverRoot'].uda = uda_root



    # add api routes

    # item/:id/thumbnail -> returns a thumbnail of the image

    info['apiRoot'].item.route('GET', (':id', 'thumbnail'), thumbnailhandler)

    # item/:id/zoomify -> returns a zoomify xml if available

    info['apiRoot'].item.route('GET', (':id', 'zoomify'), zoomifyhandler)

    # user/:userId/tasklist -> returns a list of images and any UI configuration

    info['apiRoot'].user.route('GET', (':id', 'tasklist'), tasklisthandler)

    # user/:userId/taskcomplete -> POSTable endpoint to handle completed task content

    info['apiRoot'].user.route('POST', (':id', 'taskcomplete'), taskCompleteHandler)




    # add event listeners

    events.bind('data.process', 'uploadHandler', uploadHandler)




    # add the base directory to serve



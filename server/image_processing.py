from celery import Celery

import sys

import cv2
import urllib
import numpy as np
import json
from numpy import squeeze
import Image
import cStringIO
import re
import geojson
from geojson import Polygon, Feature

# TODO: add celery, geojson to requirements.txt

c = Celery('tasks', backend='amqp', broker='amqp://')

class NumPyArangeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist() # or map(int, obj)
        return json.JSONEncoder.default(self, obj)

@c.task(name='tasks.add')
def add(x, y):
    print 'hello task'
    return x + y


@c.task(name='tasks.fillImageGeoJSON')
def fillImageGeoJSON(params):

#todo implement a smart url-based hashing cache

    # loading image from url into memory, first as np array then opencv image
    req = urllib.urlopen(params['image']['url'])

    print params['image']['url']

    arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
    img = cv2.imdecode(arr,-1) # 'load it as it is'

    h, w = img.shape[:2]
    mask = np.zeros((h+2, w+2), np.uint8)

    lo = int(params['tolerance'])
    hi = int(params['tolerance'])
    connectivity = 4
    flags = connectivity
    flags |= cv2.FLOODFILL_FIXED_RANGE

    # print 'relative', params['click']['relative']
    # print 'absolute', params['click']['absolute']

    relclick = np.asarray(params['click']['relative'])
    absclick = np.asarray(params['click']['absolute'])
    regsize = np.asarray(params['image']['region']['size'])
    region_origin = np.asarray(params['image']['region']['origin'])

    regclick = absclick - region_origin
    reg_relclick = regclick / regsize
    real_size = np.asarray([w,h])
    region_real_click = real_size * reg_relclick

    # print real_size
    # print region_real_click

    seed_pt = (int(region_real_click[0]), int(region_real_click[1]))

    # seed_pt = (int(params['click']['relative'][0] * w), int(params['click']['relative'][1] * h))
    # this doesn't work when an edge is clipped

    cv2.floodFill(img, mask, seed_pt, (255,190,00), (lo,lo,lo), (hi,hi,hi), flags)
    contours = cv2.findContours(mask,cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # contours are now defined in the coordinates of the image captured
    # to get their relative position in the subimage

    subimage_x_to_rel_subimage_x = 1. / w
    subimage_y_to_rel_subimage_y = 1. / h

    # since we know the transform of the subimage coordinate frame to the native coordinate frame

    js_region_width = float(params['image']['region']['size'][0]) # this is width in native coordinates
    js_region_height = float(params['image']['region']['size'][1]) # this is height in native coordinates

    js_region_origin_x = float(params['image']['region']['origin'][0]) # this is offset in native coordinates
    js_region_origin_y = float(params['image']['region']['origin'][1]) # this is offset in native coordinates


    def contourToGeoString(cnt):
        '''convert an opencv contour to a geojson-compatible representation'''

        t_string = []

        for pt in cnt:

            rx = subimage_x_to_rel_subimage_x * pt[0]
            ry = subimage_y_to_rel_subimage_y * pt[1]

            new_x = (js_region_width * rx) + js_region_origin_x - 3
            new_y = -1 * ((js_region_height * ry) + js_region_origin_y - 3)

            # px = np.round(pt[0] * x_scale) + bl[0]
            # py = -1*np.round(pt[1] * y_scale) + tr[1]

            t_string.append((float(new_x), float(new_y)))

        return t_string

    outer_poly = (contourToGeoString(squeeze(contours[0][0])))

    geo = Polygon([outer_poly])
    feat = Feature(geometry=geo)

    feat['properties']['rgbcolor'] = '''rgba(255, 255, 255, 0.1)'''
    feat['properties']['hexcolor'] = '''#ff0000'''
    feat['properties']['source'] = 'autofill'


    del img, mask

    return_msg = {}
    return_msg['features'] = [ geojson.dumps(feat)]

    return return_msg




#
# @c.task(name='tasks.fillImage2')
# def fillImage2(params):
#
# #todo implement a smart url-based hashing cache
#
#     # loading image from url into memory, first as np array then opencv image
#     req = urllib.urlopen(params['image']['url'])
#     arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
#     img = cv2.imdecode(arr,-1) # 'load it as it is'
#
#     h, w = img.shape[:2]
#     mask = np.zeros((h+2, w+2), np.uint8)
#
#     lo = int(params['tolerance'])
#     hi = int(params['tolerance'])
#     connectivity = 4
#     flags = connectivity
#     flags |= cv2.FLOODFILL_FIXED_RANGE
#
#
#     print 'relative', params['click']['relative']
#     print 'absolute', params['click']['absolute']
#
#     relclick = np.asarray(params['click']['relative'])
#     absclick = np.asarray(params['click']['absolute'])
#     regsize = np.asarray(params['image']['region']['size'])
#
#     region_origin = np.asarray(params['image']['region']['origin'])
#
#     regclick = absclick - region_origin
#     reg_relclick = regclick / regsize
#
#     real_size = np.asarray([w,h])
#
#     region_real_click = real_size * reg_relclick
#
#
#     print real_size
#     print region_real_click
#
#     seed_pt = (int(region_real_click[0]), int(region_real_click[1]))
#
#     # seed_pt = (int(params['click']['relative'][0] * w), int(params['click']['relative'][1] * h))
#     # this doesn't work when an edge is clipped
#
#     cv2.floodFill(img, mask, seed_pt, (255,190,00), (lo,lo,lo), (hi,hi,hi), flags)
#     contours = cv2.findContours(mask,cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
#
#     # contours are now defined in the coordinates of the image captured
#     # to get their relative position in the subimage
#
#     subimage_x_to_rel_subimage_x = 1. / w
#     subimage_y_to_rel_subimage_y = 1. / h
#
#     # since we know the transform of the subimage coordinate frame to the native coordinate frame
#
#     js_region_width = float(params['image']['region']['size'][0]) # this is width in native coordinates
#     js_region_height = float(params['image']['region']['size'][1]) # this is height in native coordinates
#
#     js_region_origin_x = float(params['image']['region']['origin'][0]) # this is offset in native coordinates
#     js_region_origin_y = float(params['image']['region']['origin'][1]) # this is offset in native coordinates
#
#     print params['image']['region']
#
#
#
#
#     def offsetPoint((x, y)):
#
#         rx = subimage_x_to_rel_subimage_x * x
#         ry = subimage_y_to_rel_subimage_y * y
#
#         new_x = (js_region_width * rx) + js_region_origin_x - 3
#         new_y = (js_region_height * ry) + js_region_origin_y - 3
#
#         return (new_x, new_y)
#
#     outer_contour = contours[0][0]
#     rescaled_contour = np.zeros_like(outer_contour)
#
#     for n, cnt in enumerate(outer_contour):
#         x,y = offsetPoint(cnt[0])
#         rescaled_contour[n, :] = [x,-y]
#
#     class NumPyArangeEncoder(json.JSONEncoder):
#         def default(self, obj):
#             if isinstance(obj, np.ndarray):
#                 return obj.tolist() # or map(int, obj)
#             return json.JSONEncoder.default(self, obj)
#
#
#     outer = json.dumps(rescaled_contour, cls=NumPyArangeEncoder)
#     # inner = json.dumps(contours[0][1], cls=NumPyArangeEncoder)
#
#     del img, mask
#
#     return_msg = {}
#     return_msg['contour'] = {
#         'outer' : outer
#     }
#
#     return return_msg





@c.task
def segmentImage(input_parameters):
    """ This function takes an input URL, seed point, and tolerance and produces a pointlist of the outer most contour
    """

    import cv2
    import numpy as np
    from numpy import unique, squeeze
    import Image
    import cStringIO
    import re
    import geojson
    from geojson import Polygon, Feature, FeatureCollection

    opdata = input_parameters

    print opdata


    imgstr = re.search(r'base64,(.*)', opdata['image']).group(1)
    tempimg = cStringIO.StringIO(imgstr.decode('base64'))
    tempimg.seek(0)
    cvimg = cv2.imdecode(np.asarray(bytearray(tempimg.read()), dtype=np.uint8), 1)
    # cv2.imwrite('inputimage.png', cvimg)

    # imgray = cv2.cvtColor(cvimg,cv2.COLOR_BGR2GRAY)
    imgray = cvimg[:,:,2]
    # cv2.imwrite('segment.png', imgray)

    all_cnts = []
    cntdict = {}

    return_data = []

    extent = opdata['extent']
    tr = extent[0]
    bl = extent[1]

    native_width = tr[0] - bl[0]
    native_height = -bl[1] + tr[1]

    x_scale = native_width / imgray.shape[1]
    y_scale = native_height / imgray.shape[0]

    def contourToGeoString(cnt):
        '''convert an opencv contour to a geojson-compatible representation'''

        t_string = []
        for pt in cnt:

            px = np.round(pt[0] * x_scale) + bl[0]
            py = -1*np.round(pt[1] * y_scale) + tr[1]

            t_string.append((float(px), float(py)))

        return t_string

    unique_labels = unique(imgray)

    print 'uniques %s' % (unique_labels)

    # we're going to make an assumption: only consider a single hole in a polygon

    for label in unique_labels:

        working_img = imgray.copy()
        working_img[working_img != label] = 0

        # CV_RETR_CCOMP retrieves all of the contours and organizes them into a two-level
        # hierarchy. At the top level, there are external boundaries of the components.
        # At the second level, there are boundaries of the holes. If there is another contour
        # inside a hole of a connected component, it is still put at the top level.

        contours, hierarchy  = cv2.findContours(working_img, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)

        # hierarchy[i][0] , hiearchy[i][1] , hiearchy[i][2] , and hiearchy[i][3] are set
        # to 0-based indices in contours of the next and previous contours at the same
        # hierarchical level, the first child contour and the parent contour, respectively.
        # If for the contour i there are no next, previous, parent, or nested contours,
        # the corresponding elements of hierarchy[i] will be negative.

        for n, cnt in enumerate(contours):

            hei = hierarchy[0][n]
    #         print hei

            # create an array for this polygon
            if str(label) not in cntdict.keys():
                cntdict[str(label)] = []

            if hei[3] >= 0:
                print '%s: %d -> this contour has a parent: %d' % (label, n, hei[3])
                # this contour has a parent, do not add it directly
                pass


            elif hei[2] < 0:
                # this contour has no children, just add it

                outer_poly = (contourToGeoString(squeeze(cnt)))

    #             x_vals = np.round(ca[:,0] * x_scale) + bl[0]
    #             y_vals = -1*np.round(ca[:,1] * y_scale) + tr[1]

                print '(add) %s: %d -> this contour (%d) has no children' % (label,n, len(outer_poly))


                print outer_poly

                geo = Polygon([outer_poly])
                feat = Feature(geometry=geo, id=len(all_cnts))
                feat['properties']['labelindex'] = str(label)


                cntdict[str(label)].append(feat)
                all_cnts.append(feat)

            else:
                # contour's child is at contours[hei[2]]
                # add this contour and it's child

                outer_poly = contourToGeoString(squeeze(cnt))
                inner_poly = contourToGeoString(squeeze(contours[hei[2]]))

                print '(add) %s: %d -> this contour (%d) has a child: %d (%d)' % (label, n, len(outer_poly), hei[2], len(inner_poly))

                geo = Polygon([outer_poly, inner_poly])

                feat = Feature(geometry=geo, id=len(all_cnts))
                feat['properties']['labelindex'] = str(label)

                cntdict[str(label)].append(feat)

                all_cnts.append(feat)


        for c in all_cnts:
            return_data.append(geojson.dumps(c))

        print 'There are %d features to return' % (len(return_data))

        # msg['features'] =

    return (return_data)



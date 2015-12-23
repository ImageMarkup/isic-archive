#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cStringIO
import json
import re

import cv2
import geojson
import numpy
# TODO: add numpy, geojson, opencv to requirements.txt

from .models.segmentation_helpers import SegmentationHelper


class NumPyArangeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, numpy.ndarray):
            return obj.tolist()  # or map(int, obj)
        return json.JSONEncoder.default(self, obj)



def fillImageGeoJSON(image_data, seed_point, tolerance):
    if not(
        # note, the image_data has a shape of (rows, cols), the seed is (x, y)
        0.0 <= seed_point[0] <= image_data.shape[1] and
        0.0 <= seed_point[1] <= image_data.shape[0]
    ):
        # TODO: a proper out of bounds error
        return {'error': 'out of bounds'}

    contour = SegmentationHelper.segment(image_data, seed_point, tolerance)

    feat = geojson.Feature(
        # TODO: can this be made a LineString?
        # geometry=geojson.LineString(coordinates=tuple(contour.tolist())),
        geometry=geojson.Polygon(coordinates=(contour.tolist(),)),
        properties={
            'rgbcolor': 'rgba(255, 255, 255, 0.1)',
            'hexcolor': '#ff0000',
            'source': 'autofill'
        }
    )
    return {
        'features': [feat]
    }


def segmentImage(input_parameters):
    """
    This function takes an input URL, seed point, and tolerance and produces a
    pointlist of the outer-most contour
    """
    opdata = input_parameters

    imgstr = re.search(r'base64,(.*)', opdata['image']).group(1)
    tempimg = cStringIO.StringIO(imgstr.decode('base64'))
    tempimg.seek(0)
    cvimg = cv2.imdecode(numpy.asarray(bytearray(tempimg.read()), dtype=numpy.uint8), 1)
    # cv2.imwrite('inputimage.png', cvimg)

    # imgray = cv2.cvtColor(cvimg,cv2.COLOR_BGR2GRAY)
    imgray = cvimg[:, :, 2]
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

    def contourToGeoString(contour):
        """
        convert an OpenCV contour to a geojson-compatible representation
        """
        t_string = []
        for pt in contour:

            px = numpy.round(pt[0] * x_scale) + bl[0]
            py = -1 * numpy.round(pt[1] * y_scale) + tr[1]

            t_string.append((float(px), float(py)))

        return t_string

    unique_labels = numpy.unique(imgray)

    # we're going to make an assumption: only consider a single hole in a polygon

    for label in unique_labels:

        working_img = imgray.copy()
        working_img[working_img != label] = 0

        # CV_RETR_CCOMP retrieves all of the contours and organizes them into a two-level
        # hierarchy. At the top level, there are external boundaries of the components.
        # At the second level, there are boundaries of the holes. If there is another contour
        # inside a hole of a connected component, it is still put at the top level.

        contours, hierarchy = cv2.findContours(working_img, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)

        # hierarchy[i][0] , hiearchy[i][1] , hiearchy[i][2] , and hiearchy[i][3] are set
        # to 0-based indices in contours of the next and previous contours at the same
        # hierarchical level, the first child contour and the parent contour, respectively.
        # If for the contour i there are no next, previous, parent, or nested contours,
        # the corresponding elements of hierarchy[i] will be negative.

        for n, cnt in enumerate(contours):

            hei = hierarchy[0][n]

            # create an array for this polygon
            if str(label) not in cntdict.keys():
                cntdict[str(label)] = []

            if hei[3] >= 0:
                # print '%s: %d -> this contour has a parent: %d' % (label, n, hei[3])
                # this contour has a parent, do not add it directly
                pass

            elif hei[2] < 0:
                # this contour has no children, just add it

                outer_poly = (contourToGeoString(numpy.squeeze(cnt)))

    #             x_vals = numpy.round(ca[:,0] * x_scale) + bl[0]
    #             y_vals = -1*numpy.round(ca[:,1] * y_scale) + tr[1]

                # print '(add) %s: %d -> this contour (%d) has no children' % (label,n, len(outer_poly))

                feat = geojson.Feature(
                    geometry=geojson.Polygon((outer_poly,)),
                    id=len(all_cnts),
                    properties={
                        'labelindex': str(label)
                    }
                )


                cntdict[str(label)].append(feat)
                all_cnts.append(feat)

            else:
                # contour's child is at contours[hei[2]]
                # add this contour and it's child

                outer_poly = contourToGeoString(numpy.squeeze(cnt))
                inner_poly = contourToGeoString(numpy.squeeze(contours[hei[2]]))

                # print '(add) %s: %d -> this contour (%d) has a child: %d (%d)' % (label, n, len(outer_poly), hei[2], len(inner_poly))

                feat = geojson.Feature(
                    geometry=geojson.Polygon((outer_poly, inner_poly)),
                    id=len(all_cnts),
                    properties={
                        'labelindex': str(label)
                    }
                )

                cntdict[str(label)].append(feat)

                all_cnts.append(feat)

        for c in all_cnts:
            return_data.append(geojson.dumps(c))

    return return_data

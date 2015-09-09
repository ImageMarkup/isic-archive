#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cStringIO
import json
import re

import cv2
import geojson
import numpy

# TODO: add numpy, geojson, opencv to requirements.txt


class NumPyArangeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, numpy.ndarray):
            return obj.tolist()  # or map(int, obj)
        return json.JSONEncoder.default(self, obj)


def segmentConnectedRegion(image, seed, tolerance):
    return _segmentConnectedRegionCV(image, seed, tolerance)


def _segmentConnectedRegionSK(image, seed, tolerance):
    """
    SciKit Image implementation
    """
    # TODO
    # threshold step
    # http://scikit-image.org/docs/stable/api/skimage.measure.html#label
    pass


def _segmentConnectedRegionCV(image, seed, tolerance,
                              connectivity=8, fill_value=1):
    """
    Segment an image into a region connected to a seed point, using OpenCV.

    :param image: The image to be segmented.
    :type image: numpy.ndarray
    :param seed: The point inside the connected region where the
    segmentation will start.
    :type seed: list
    :param tolerance: The maximum color/intensity difference between the seed
    point and a point in the connected region.
    :type tolerance: int
    :param connectivity: (optional) The number of allowed connectivity
    propagation directions. Allowed values are:
      * 4 for edge pixels
      * 8 for edge and corner pixels
    :type connectivity: int
    :param fill_value: (optional)  The value to fill in the mask for pixels
    that are part of the connected region. Should be non-zero.
    :type fill_value: int
    :returns: A binary label mask, with an extra 1-pixel wide padded border.
    The values are either ``0`` or ``fill_value``.
    :rtype: numpy.ndarray
    """
    image_height, image_width, image_channels = image.shape
    # create padded mask to store output
    mask = numpy.zeros((image_height + 2, image_width + 2), numpy.uint8)

    flags = 0
    flags |= connectivity
    flags |= (fill_value << 8)
    # compare each candidate to the seed, not its nearest neighbor; for lesion
    #   images the gradient is too shallow for even very small tolerances to
    #   work with a neared neighbor comparison
    flags |= cv2.FLOODFILL_FIXED_RANGE

    area, (bounds_x, bounds_y, bounds_width, bounds_height) = cv2.floodFill(
        image=image,
        mask=mask,
        seedPoint=tuple(seed),
        newVal=(255, 190, 00),  # TODO: why this?
        loDiff=(tolerance,) * 3,
        upDiff=(tolerance,) * 3,
        flags=flags
    )

    # we could remove the padding, but cv2.findContours requires it to be present
    # mask = mask[1:-1, 1:-1]

    return mask


def extractContour(image_mask):
    return _extractContourCV(image_mask)


def _extractContourSK(image_mask):
    """
    SciKit Image implementation
    """
    # TODO
    pass


def _extractContourCV(image_mask, safe=True, smoothing=False):
    """
    Extract the contour line within a segmented label mask, using OpenCV.

    :param image_mask: A binary label mask, with an extra 1-pixel wide padded
    border. Values are considered as only 0 or non-0.
    :type image_mask: numpy.ndarray
    :param safe: Guarantee that the image_mask will not be modified. This is slower.
    :type safe: bool
    :param smoothing: Use a Teh-Chin chain approximation algorithm to slightly
    smooth and collapse the contour.
    :type smoothing: bool
    :return: An array of point pairs.
    :rtype: numpy.ndarray
    """
    if safe:
        image_mask = numpy.copy(image_mask)

    if smoothing:
        # TODO: determine which one to use (or add parameter for either)
        # approx_method = cv2.CHAIN_APPROX_TC89_L1
        approx_method = cv2.CHAIN_APPROX_TC89_KCOS
    else:
        approx_method = cv2.CHAIN_APPROX_SIMPLE

    contours, hierarchy = cv2.findContours(
        image=image_mask,
        mode=cv2.RETR_EXTERNAL,
        method=approx_method,
        # compensate for the image's 1-pixel padding
        offset=(-1, -1)
    )

    # "cv2.RETR_EXTERNAL" means there's only one contour
    contour = contours[0]
    # contour initially looks like [ [[0,1]], [[0,2]] ], so squeeze it
    contour = numpy.squeeze(contour)
    return contour


def fillImageGeoJSON(image_data, seed_point, tolerance):
    if not(
        # note, the image_data has a shape of (rows, cols), the seed is (x, y)
        0.0 <= seed_point[0] <= image_data.shape[1] and
        0.0 <= seed_point[1] <= image_data.shape[0]
    ):
        # TODO: a proper out of bounds error
        return {'error': 'out of bounds'}

    image_mask = segmentConnectedRegion(image_data, seed_point, tolerance)
    contour = extractContour(image_mask)

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

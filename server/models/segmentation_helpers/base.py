#!/usr/bin/env python
# -*- coding: utf-8 -*-


class BaseSegmentationHelper(object):
    @classmethod
    def loadImage(cls, image_data):
        raise NotImplementedError()

    @classmethod
    def segment(cls, image, seed_coord, tolerance):
        raise NotImplementedError()

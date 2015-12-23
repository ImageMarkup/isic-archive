#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from .opencv import OpenCVSegmentationHelper as SegmentationHelper
except ImportError:
    try:
        from .scikit import ScikitSegmentationHelper as SegmentationHelper
    except ImportError:
        raise ImportError('Could not load OpenCV or Scikit-Image.')

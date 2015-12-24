#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from .opencv import OpenCVSegmentationHelper
except ImportError:
    raise ImportError('Could not load OpenCV.')

try:
    from .scikit import ScikitSegmentationHelper
except ImportError:
    raise ImportError('Could not load Scikit-Image.')

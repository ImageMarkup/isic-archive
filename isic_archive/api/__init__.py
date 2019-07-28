#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#  Copyright Kitware Inc.
#
#  Licensed under the Apache License, Version 2.0 ( the "License" );
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
###############################################################################

from .annotation import AnnotationResource  # noqa:F401
from .dataset import DatasetResource  # noqa:F401
from .image import ImageResource  # noqa:F401
from .redirects import RedirectsResource  # noqa:F401
from .segmentation import SegmentationResource  # noqa:F401
from .study import StudyResource  # noqa:F401
from .task import TaskResource  # noqa:F401
from .user import attachUserApi  # noqa:F401

__all__ = ['AnnotationResource', 'DatasetResource', 'ImageResource',
           'SegmentationResource', 'StudyResource', 'TaskResource', 'attachUserApi']

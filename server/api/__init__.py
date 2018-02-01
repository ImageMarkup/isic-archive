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

# Deal with a bug where PEP257 crashes when parsing __all__
# flake8: noqa

from .annotation import AnnotationResource
from .dataset import DatasetResource
from .image import ImageResource
from .segmentation import SegmentationResource
from .study import StudyResource
from .task import TaskResource
from .user import attachUserApi

__all__ = [AnnotationResource, DatasetResource, ImageResource,
           SegmentationResource, StudyResource, TaskResource, attachUserApi]

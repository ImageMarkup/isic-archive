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

import os
import json

import cherrypy
import execjs
from querylang import astToMongo

from girder.api.rest import RestException
from girder.utility.model_importer import ModelImporter


TRUE_VALUES = set([True, 'true', 1, 'True'])


class HistogramUtility(object):
    def __init__(self):
        # Load up the external foreign code snippets
        self.foreignCode = {}

        codePath = os.path.dirname(__file__)

        for filename in os.listdir(codePath):
            extension = os.path.splitext(filename)[1]
            if extension in ['.js', '.json']:
                with open(os.path.join(codePath, filename), 'rb') as infile:
                    self.foreignCode[filename] = infile.read()

    def mapReduce(self, collection, mapScript, reduceScript, params={}):
        # Convert our AST filter expression to a mongo filter
        query = None
        if 'filter' in params and params['filter'] is not None:
            query = astToMongo(params['filter'])
        mr_result = collection.inline_map_reduce(mapScript,
                                                 reduceScript,
                                                 query=query,
                                                 scope={
                                                     'counter': -1,
                                                     'params': params
                                                 })
        # rearrange into a neater dict before sending it back
        result = {}
        for r in mr_result:
            # TODO: remove fields not specified in the fields parameter
            # (or is there a more efficient way to keep them out of
            # the results in the first place?)
            result[r['_id']] = r['value']

        return result

    def addFolderFilters(self, filterSpec, validFolders):
        folderFilter = {
            'operator': 'in',
            'operands': [
                {
                    'identifier': 'folderId',
                    'type': 'string'
                },
                validFolders
            ]
        }
        if filterSpec is None:
            return folderFilter
        else:
            return {
                'operator': 'and',
                'operands': [
                    folderFilter,
                    filterSpec
                ]
            }

    def hardCodeBinSettings(self, params):
        """
        Here we hard-code settings about which attributes we want, and how to
        retrieve them. For details on the meaning of these settings, see the
        description text for getHistograms() in
        https://github.com/Kitware/candela/blob/master/app/resonant-laboratory/server/datasetItem.py

        In the future, it should be easy to adapt inferSchema() in the same file
        to auto-detect this information instead of hard-coding it.
        """
        params['binSettings'] = json.dumps({
            'folderId': {
                'coerceToType': 'string'
            },
            'meta.clinical.benign_malignant': {
                'coerceToType': 'string'
            },
            'meta.clinical.sex': {
                'coerceToType': 'string'
            },
            'meta.clinical.age': {
                'coerceToType': 'number',
                'interpretation': 'ordinal',
                'lowBound': 0,
                'highBound': 100,
                'numBins': 10
            },
            'meta.clinical.clin_size_long_diam_mm': {
                'coerceToType': 'number',
                'interpretation': 'ordinal',
                'lowBound': 0,
                'highBound': 100,
                'numBins': 10
            },
            'meta.clinical.personal_hx_mm': {
                'coerceToType': 'string'
            },
            'meta.clinical.family_hx_mm': {
                'coerceToType': 'string'
            }
        })

        return params

    def fillInDefaultHistogramParams(self, params):
        # Populate params with default settings
        # where settings haven't been specified
        params['filter'] = params.get('filter', None)
        if params['filter'] is not None:
            params['filter'] = json.loads(params['filter'])
        params['limit'] = params.get('limit', None)
        if params['limit'] == 0:
            params['limit'] = None
        params['offset'] = params.get('offset', 0)

        binSettings = json.loads(params.get('binSettings', '{}'))
        for attrName in binSettings.iterkeys():
            binSettings[attrName] = binSettings.get(attrName, {})

            # Get user-defined or default type coercion setting
            coerceToType = binSettings[attrName].get('coerceToType', 'object')
            binSettings[attrName]['coerceToType'] = coerceToType

            # Get user-defined or default interpretation setting
            if binSettings[attrName]['coerceToType'] is 'object':
                interpretation = binSettings[attrName]['interpretation'] = \
                    'categorical'
            else:
                interpretation = binSettings[attrName].get(
                    'interpretation', 'categorical')
                binSettings[attrName]['interpretation'] = interpretation

            # Get any user-defined special bins (the defaults are
            # listed in histogram_reduce.js)
            specialBins = json.loads(binSettings[attrName].get(
                'specialBins', '[]'))
            binSettings[attrName]['specialBins'] = specialBins

            # Get user-defined or default number of bins
            numBins = binSettings[attrName].get('numBins', 10)
            binSettings[attrName]['numBins'] = numBins

            # For ordinal binning, we need some more details:
            if interpretation == 'ordinal':
                if coerceToType == 'string' or coerceToType == 'object':
                    # Use the locale to construct the bins
                    lowBound = None
                    highBound = None
                    locale = binSettings[attrName].get('locale', None)
                    if locale is None:
                        # Default is to try to extract locale information
                        # from the Accept-Language header, with 'en' as
                        # a backup (TODO: do smarter things with alternative
                        # locales)
                        locale = cherrypy.request.headers.get(
                            'Accept-Language', 'en')
                        if ',' in locale:
                            locale = locale.split(',')[0].strip()
                        if ';' in locale:
                            locale = locale.split(';')[0].strip()
                else:
                    # Use default or user-defined low/high boundary values
                    # to construct the bins
                    locale = None
                    lowBound = binSettings[attrName].get('lowBound', None)
                    highBound = binSettings[attrName].get('highBound', None)
                    if lowBound is None or highBound is None:
                        raise RestException(
                            'There are no observed values of type %s, so it is '
                            'impossible to automatically determine low/high '
                            'bounds for an ordinal interpretation. Please '
                            'supply bounds or change to "categorical".' %
                            coerceToType)
                    binSettings[attrName]['lowBound'] = lowBound
                    binSettings[attrName]['highBound'] = highBound

                # Pre-populate the bins with human-readable names
                binUtilsCode = execjs.compile(
                    'var LOCALE_INDEXES = %s;\n%s' % (
                        self.foreignCode['localeIndexes.json'],
                        self.foreignCode['binUtils.js']))
                binSettings[attrName]['ordinalBins'] = binUtilsCode.call(
                    'createBins', coerceToType, numBins, lowBound, highBound,
                    locale)['bins']
            else:
                pass
                # We can ignore the ordinalBins parameter if we're being
                # categorical.
                # TODO: the fancier 2-pass idea in histogram_reduce.js
                # would necessitate that we do something different here

        params['binSettings'] = binSettings
        params['cache'] = params.get('cache', False) in TRUE_VALUES

        return params, binSettings

    def getHistograms(self, user, params):
        Image = ModelImporter.model('image', 'isic_archive')
        Dataset = ModelImporter.model('dataset', 'isic_archive')

        params = self.hardCodeBinSettings(params)
        params, binSettings = self.fillInDefaultHistogramParams(params)

        collection = Image.collection

        # Limit to folders that user has access to
        validFolders = [dataset['_id'] for dataset in Dataset.list(user=user)]
        params['filter'] = self.addFolderFilters(params['filter'], validFolders)

        # Construct and run the histogram MapReduce code
        mapScript = 'function map () {\n' + \
            self.foreignCode['binUtils.js'] + '\n' + \
            self.foreignCode['histogram_map.js'] + '\n}'

        reduceScript = 'function reduce (attrName, allHistograms) {\n' + \
            self.foreignCode['histogram_reduce.js'] + '\n' + \
            'return {histogram: histogram};\n}'

        histogram = self.mapReduce(collection, mapScript, reduceScript, params)

        # We have to clean up the histogram wrappers (mongodb can't return
        # an array from reduce functions). While we're at it, add the
        # lowBound / highBound details to each ordinal bin
        for attrName, wrappedHistogram in histogram.iteritems():
            histogram[attrName] = wrappedHistogram['histogram']

        if '__passedFilters__' not in histogram:
            # This will only happen if there's a count of zero;
            # the __passedFilters__ bin will never have been emitted
            histogram['__passedFilters__'] = [{
                'count': 0,
                'label': 'count'
            }]

        return histogram

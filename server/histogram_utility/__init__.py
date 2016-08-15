import os
import json
from querylang import astToMongo


class HistogramUtility():
    def __init__(self):
        # Load up the external foreign code snippets
        self.foreignCode = {}

        codePath = 'plugins/isic_archive/server/histogram_utility'
        codePath = os.path.join(os.getcwd(), codePath)

        for filename in os.listdir(codePath):
            extension = os.path.splitext(filename)[1]
            if extension != '.js' and extension != '.json':
                continue
            infile = open(os.path.join(codePath, filename), 'rb')
            self.foreignCode[filename] = infile.read()
            infile.close()

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

    def fillInDefaultParams(self, params):
        # Populate params with default settings
        # where settings haven't been specified
        params['filter'] = params.get('filter', None)
        if params['filter'] is not None:
            params['filter'] = json.loads(params['filter'])
        params['limit'] = params.get('limit', 0)
        params['offset'] = params.get('offset', 0)

        '''
        Here we hard-code settings about which attributes we want, and how to
        retrieve them. For details on the meaning of these settings, see the
        description text for getHistograms() in
        https://github.com/Kitware/candela/blob/master/app/resonant-laboratory/server/datasetItem.py

        In the future, it should be easy to adapt inferSchema() in the same file
        to auto-detect this information.
        '''
        params['binSettings'] = {
            'folderId': {
                'coerceToType': 'string'
            },
            'acquisition.pixelsX': {
                'coerceToType': 'integer'
            },
            'acquisition.pixelsY': {
                'coerceToType': 'integer'
            },
            'meta.clinical.benign_malignant': {
                'coerceToType': 'string'
            },
            'meta.clinical.sex': {
                'coerceToType': 'string'
            },
            'meta.clinical.age': {
                'coerceToType': 'number',
                'lowBound': 0,
                'highBound': 100,
                'binCount': 10
            }
        }

        return params

    def getHistograms(self, collection, params):
        params = self.fillInDefaultParams(params)
        binSettings = params['binSettings']

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
            if attrName in binSettings and 'ordinalBins' in binSettings[attrName]:
                for binIndex, binObj in enumerate(binSettings[attrName]['ordinalBins']):
                    histogram[attrName][binIndex]['lowBound'] = binObj['lowBound']
                    histogram[attrName][binIndex]['highBound'] = binObj['highBound']

        if '__passedFilters__' not in histogram:
            # This will only happen if there's a count of zero;
            # the __passedFilters__ bin will never have been emitted
            histogram['__passedFilters__'] = [{
                'count': 0,
                'label': 'count'
            }]

        return histogram

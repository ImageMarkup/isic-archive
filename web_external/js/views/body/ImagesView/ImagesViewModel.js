// This is a pure, backbone-only helper model (i.e. not the same thing
// as the stuff in js/models)

isic.views.ImagesViewSubViews = isic.views.ImagesViewSubViews || {};
isic.views.ImagesViewSubViews.ImagesViewModel = Backbone.Model.extend({
    defaults: {
        limit: 50,
        offset: 0,
        selectedImageId: null,
        filter: {
            standard: {},
            custom: []
        },
        imageIds: [],
        overviewHistogram: {
            __passedFilters__: [{
                count: 0,
                label: 'count'
            }]
        },
        studyHistogram: {
            __passedFilters__: [{
                count: 0,
                label: 'count'
            }]
        },
        filteredSetHistogram: {
            __passedFilters__: [{
                count: 0,
                label: 'count'
            }]
        },
        pageHistogram: {
            __passedFilters__: [{
                count: 0,
                label: 'count'
            }]
        }
    },
    initialize: function () {
        var self = this;

        self.updateHistogram('overview');
        self.updateHistogram('filteredSet').then(function () {
            return self.updateCurrentPage();
        }).then(function () {
            return self.updateHistogram('page');
        });

        self.listenTo(self, 'change:limit', self.updateCurrentPage);
        self.listenTo(self, 'change:offset', self.updateCurrentPage);
        self.listenTo(self, 'change:filter', self.updateCurrentPage);
        self.listenTo(self, 'change:imageIds', function () {
            self.set('selectedImageId', null);
        });
    },
    updateHistogram: function (histogramName) {
        var self = this;
        var requestParams = {};

        /*
        TODO: send parameters, depending on which type of histogram that we want
        if (histogramName === 'page') {
            requestParams.limit = self.get('limit');
            requestParams.offset = self.get('offset');
        }
        if (histogramName === 'page' || histogramName === 'filteredSet') {
            requestParams.filter = self.getFilterString();
        }
        */
        return girder.restRequest({
            path: 'image/histogram',
            data: requestParams
        }).then(function (resp) {
            self.set(histogramName + 'Histogram',
                self.postProcessHistogram(resp));
        });
    },
    updateCurrentPage: function () {
        var self = this;

        // Construct the parameters to send to the server
        var requestParams = self.getPageDetails(true);

        // First cap the page size by how many images are available
        requestParams.limit = Math.min(requestParams.filteredSetCount,
            requestParams.limit);
        // The page must include at least one image
        requestParams.limit = Math.max(1, requestParams.limit);
        // Don't allow pages of more than 250 images
        requestParams.limit = Math.min(250, requestParams.limit);

        // Can't have a negative offset
        requestParams.offset = Math.max(0, requestParams.offset);
        // Limit the last page by how many images are available
        if (requestParams.offset + requestParams.limit >
                requestParams.filteredSetCount) {
            requestParams.offset = Math.floor(
                requestParams.filteredSetCount / requestParams.limit) *
                requestParams.limit;
        }

        // In case we've overridden anything, update with the cleaned values
        self.set(requestParams, {silent: true}); // eslint-disable-line no-silent

        // TODO: pass in filter settings
        // var filterString = self.getFilterString();
        return girder.restRequest({
            path: 'image',
            data: requestParams
        }).then(function (resp) {
            self.set('imageIds', resp.map(function (imageObj) {
                return imageObj._id;
            }));
        });
    },
    getPageDetails: function (skipLimitCap) {
        var self = this;
        var result = {
            overviewCount: self.get('overviewHistogram').__passedFilters__[0].count,
            filteredSetCount: self.get('filteredSetHistogram').__passedFilters__[0].count,
            offset: self.get('offset'),
            limit: self.get('limit')
        };
        if (!skipLimitCap &&
                result.offset + result.limit > result.filteredSetCount) {
            result.limit = result.filteredSetCount - result.offset;
        }
        return result;
    },
    postProcessHistogram: function (histogram) {
        var self = this;
        var formatter = d3.format('0.3s');
        // If the user is logged out, we'll sometimes get an
        // empty histogram back
        if (!('__passedFilters__' in histogram)) {
            return null;
        }
        Object.keys(histogram).forEach(function (attrName) {
            histogram[attrName].forEach(function (bin, index) {
                if (typeof bin.lowBound === 'number' &&
                        typeof bin.highBound === 'number') {
                    // binUtils.js doesn't have access to D3's superior number
                    // formatting abilities, so we patch on slightly better
                    // human-readable labels
                    bin.label = '[' + formatter(bin.lowBound) + ' - ' +
                        formatter(bin.highBound);
                    if (index === histogram[attrName].length - 1) {
                        bin.label += ']';
                    } else {
                        bin.label += ')';
                    }
                }
            });
        });
        return histogram;
    },
    autoDetectAttributeInterpretation: function (attrName) {
        var self = this;
        // Go with the default interpretation for the attribute type
        return window.ENUMS.DEFAULT_INTERPRETATIONS[self.getAttributeType(attrName)];
    },
    getAttributeInterpretation: function (attrName) {
        var self = this;
        var attrSpec = window.ENUMS.SCHEMA[attrName];
        if (attrSpec.interpretation) {
            // The user has specified an interpretation
            return attrSpec.interpretation;
        } else {
            // auto-detect the interpretation
            return self.autoDetectAttributeInterpretation(attrName);
        }
    },
    autoDetectAttributeType: function (attrName) {
        var self = this;
        var attrSpec = window.ENUMS.SCHEMA[attrName];
        // Find the most specific type that can accomodate all the values
        var attrType = 'object';
        var count = 0;
        var dataType;
        window.ENUMS.ATTRIBUTE_GENERALITY.forEach(function (dataType) {
          if (attrSpec.hasOwnProperty(dataType) &&
                attrSpec[dataType].count >= count) {
              attrType = dataType;
              count = attrSpec[dataType].count;
          }
        });
        return attrType;
    },
    getAttributeType: function (attrName) {
        var self = this;
        var attrSpec = window.ENUMS.SCHEMA[attrName];
        if (attrSpec.coerceToType) {
            // The user has specified a data type
            return attrSpec.coerceToType;
        } else {
            // auto-detect the data type
            return self.autoDetectAttributeType(attrName);
        }
    },
    getBinStatus: function (attrName, bin) {
        var self = this;
        // Easy check (that also validates whether filter.standard[attrName]
        // even exists)
        var filterState = self.getFilteredState(attrName);
        if (filterState === window.ENUMS.FILTER_STATES.NO_FILTERS) {
            return window.ENUMS.BIN_STATES.INCLUDED;
        }

        var filterSpec = self.get('filter').standard[attrName];

        // Next easiest check: is the label not in the include list (if there is
        // one) / in the list that is specifically excluded?
        if (filterSpec.includeValues &&
                filterSpec.includeValues.indexOf(bin.label) === -1) {
            return window.ENUMS.BIN_STATES.EXCLUDED;
        } else if (filterSpec.excludeValues &&
                filterSpec.excludeValues.indexOf(bin.label) !== -1) {
            return window.ENUMS.BIN_STATES.EXCLUDED;
        }

        // Trickiest check: is the range excluded (or partially excluded)?
        if (filterSpec.excludeRanges &&
                bin.hasOwnProperty('lowBound') &&
                bin.hasOwnProperty('highBound')) {
            // Make sure to use proper string comparisons if this is a string bin
            var comparator;
            if (self.getAttributeType(attrName) === 'string') {
                comparator = function (a, b) {
                    return a.localeCompare(b);
                }
            }
            // Intersect the bin with the excluded values
            var includedRanges = window.shims.RangeSet.rangeSubtract([{
                    lowBound: bin.lowBound,
                    highBound: bin.highBound
                }], filterSpec.excludeRanges, comparator);

            if (includedRanges.length === 1 &&
                    includedRanges[0].lowBound === bin.lowBound &&
                    includedRanges[0].highBound === bin.highBound) {
                // Wound up with the same range we started with;
                // the whole bin is included
                return window.ENUMS.BIN_STATES.INCLUDED;
            } else if (includedRanges.length > 0) {
                // Only a piece survived; this is a partial!
                return window.ENUMS.BIN_STATES.PARTIAL;
            } else {
                // Nothing survived the subtraction; this bin
                // is excluded
                return window.ENUMS.BIN_STATES.EXCLUDED;
            }
        }

        // No filter info left to check; the bin must be included
        return window.ENUMS.BIN_STATES.INCLUDED;
    },
    applyFilter: function (filter) {
        var self = this;
        // Clean up the filter specification
        var standardKeys = Object.keys(filter.standard);
        standardKeys.forEach(function (k) {
            var removeFilterSpec = !(filter.standard[k].hasOwnProperty('excludeAttribute'));
            ['excludeRanges', 'includeValues', 'excludeValues'].forEach(function (d) {
                if (filter.standard[k].hasOwnProperty(d)) {
                    if (filter.standard[k][d].length === 0) {
                        delete filter.standard[k][d];
                    } else {
                        removeFilterSpec = false;
                    }
                }
            });
            if (removeFilterSpec) {
                delete filter.standard[k];
            }
        });

        self.set('filter', filter);
    },
    clearFilters: function (attrName) {
        var self = this;
        var filter = self.get('filter');
        if (filter.standard.hasOwnProperty(attrName)) {
            delete filter.standard[attrName].excludeRanges;
            delete filter.standard[attrName].excludeValues;
            delete filter.standard[attrName].includeValues;
            self.applyFilter(filter);
        }
    },
    selectRange: function (attrName, lowBound, highBound) {
        var self = this;
        var filter = self.get('filter');
        // Temporarily init a filter object for this attribute
        // if it doesn't already exist
        if (!filter.standard[attrName]) {
            filter.standard[attrName] = {};
        }

        // Include ONLY the values in the indicated range, AKA
        // exclude everything outside it
        filter.standard[attrName].excludeRanges = [
            { highBound: lowBound },
            { lowBound: highBound }
        ];

        self.applyFilter(filter);
    },
    removeRange: function (attrName, lowBound, highBound, comparator) {
        var self = this;
        var filter = self.get('filter');
        // Temporarily init a filter object for this attribute
        // if it doesn't already exist
        if (!filter.standard[attrName]) {
            filter.standard[attrName] = {};
        }

        var excludeRanges = filter.standard[attrName].excludeRanges || [];
        var range = {};
        if (lowBound !== undefined) {
            range.lowBound = lowBound;
        }
        if (highBound !== undefined) {
            range.highBound = highBound;
        }
        excludeRanges = window.shims.RangeSet.rangeUnion(
            excludeRanges, [range], comparator);
        filter.standard[attrName].excludeRanges = excludeRanges;

        self.applyFilter(filter);
    },
    includeRange: function (attrName, lowBound, highBound, comparator) {
        var self = this;
        var filter = self.get('filter');
        // Temporarily init a filter object for this attribute
        // if it doesn't already exist
        if (!filter.standard[attrName]) {
            filter.standard[attrName] = {};
        }

        var excludeRanges = filter.standard[attrName].excludeRanges || [];
        var range = {};
        if (lowBound !== undefined) {
            range.lowBound = lowBound;
        }
        if (highBound !== undefined) {
            range.highBound = highBound;
        }
        excludeRanges = window.shims.RangeSet.rangeSubtract(
            excludeRanges, [range], comparator);
        filter.standard[attrName].excludeRanges = excludeRanges;

        self.applyFilter(filter);
    },
    selectValues: function (attrName, values) {
        var self = this;
        var filter = self.get('filter');
        // Temporarily init a filter object for this attribute
        // if it doesn't already exist
        if (!filter.standard[attrName]) {
            filter.standard[attrName] = {};
        }

        // Select ONLY the given values
        filter.standard[attrName].includeValues = values;
        delete filter.standard[attrName].excludeValues;

        self.applyFilter(filter);
    },
    removeValue: function (attrName, value) {
        var self = this;
        var filter = self.get('filter');
        // Temporarily init a filter object for this attribute
        // if it doesn't already exist
        if (!filter.standard[attrName]) {
            filter.standard[attrName] = {};
        }

        var excludeValues = filter.standard[attrName].excludeValues || [];
        var valueIndex = excludeValues.indexOf(value);
        if (valueIndex === -1) {
            excludeValues.push(value);
        }
        filter.standard[attrName].excludeValues = excludeValues;
        delete filter.standard[attrName].includeValues;

        self.applyFilter(filter);
    },
    includeValue: function (attrName, value) {
        // Temporarily init a filter object for this attribute
        // if it doesn't already exist
        if (!filter.standard[attrName]) {
            filter.standard[attrName] = {};
        }

        var excludeValues = filter.standard[attrName].excludeValues || [];
        var valueIndex = excludeValues.indexOf(value);
        if (valueIndex !== -1) {
            excludeValues.splice(valueIndex, 1);
        }
        filter.standard[attrName].excludeValues = excludeValues;
        delete filter.standard[attrName].includeValues;

        self.applyFilter(filter);
    },
    getFilteredState: function (attrName) {
        var self = this;
        var filter = self.get('filter');
        if (filter.standard[attrName]) {
            if (filter.standard[attrName].excludeAttribute) {
                return window.ENUMS.FILTER_STATES.EXCLUDED;
            } else {
                return window.ENUMS.FILTER_STATES.FILTERED;
            }
        } else {
            return window.ENUMS.FILTER_STATES.NO_FILTERS;
        }
    }
});

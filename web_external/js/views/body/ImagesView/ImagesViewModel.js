/*globals d3, peg*/

// This is a pure, backbone-only helper model (i.e. not the same thing
// as the stuff in js/models)

isic.views.ImagesViewSubViews = isic.views.ImagesViewSubViews || {};
isic.views.ImagesViewSubViews.ImagesViewModel = Backbone.Model.extend({
    defaults: {
        limit: 50,
        offset: 0,
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

        this.datasetCollection = new isic.collections.DatasetCollection();

        // Load the pegjs grammar and fetch the datasets
        // before attempting to get histograms or image IDs
        $.when(self.fetchDatasets(), self.loadFilterGrammar())
            .then(function () {
                // We need the study names before getting any histograms
                self.updateHistogram('overview');
                // We need the study names and the filter grammar before getting
                // the filtered set or the current page (both the page of images
                // and the page histogram)
                self.updateFilters();
            });

        self.listenTo(self, 'change:limit', self.updateCurrentPage);
        self.listenTo(self, 'change:offset', self.updateCurrentPage);
        self.listenTo(self, 'change:filter', self.updateFilters);
    },
    fetchDatasets: function () {
        var deferred = $.Deferred();
        this.datasetCollection.once('g:changed', function () {
            deferred.resolve();
        }).fetch();
        return deferred.promise();
    },
    loadFilterGrammar: function () {
        var self = this;
        return $.ajax({
            url: girder.staticRoot + '/built/plugins/isic_archive/extra/query.pegjs',
            dataType: 'text',
            success: function (data) {
                self.astParser = peg.generate(data);
            }
        });
    },
    updateHistogram: function (histogramName) {
        var self = this;
        var pageDetails = self.getPageDetails();
        var requestParams = {};

        if (histogramName === 'page') {
            requestParams.limit = pageDetails.limit;
            requestParams.offset = pageDetails.offset;
        }
        if (histogramName === 'page' || histogramName === 'filteredSet') {
            requestParams.filter = JSON.stringify(self.getFilterAstTree());
        }
        return girder.restRequest({
            path: 'image/histogram',
            data: requestParams
        }).then(function (resp) {
            self.set(histogramName + 'Histogram',
                self.postProcessHistogram(resp));
        });
    },
    updateFilters: function () {
        var self = this;
        return $.when(self.updateHistogram('filteredSet'),
                           self.updateCurrentPage());
    },
    updateCurrentPage: function () {
        var self = this;

        // Construct the parameters to send to the server
        var pageDetails = self.getPageDetails();

        // The page must include at least one image
        pageDetails.limit = Math.max(1, pageDetails.limit);
        // Don't allow pages of more than 250 images
        pageDetails.limit = Math.min(250, pageDetails.limit);

        // Can't have a negative offset
        pageDetails.offset = Math.max(0, pageDetails.offset);
        // Limit the last page by how many images are available
        if (pageDetails.offset + pageDetails.limit >
                pageDetails.filteredSetCount) {
            pageDetails.offset = Math.floor(
                pageDetails.filteredSetCount / pageDetails.limit) *
                pageDetails.limit;
        }

        // In case we've overridden anything, update with the cleaned values
        self.set({
            limit: pageDetails.limit,
            offset: pageDetails.offset
        }, {silent: true}); // eslint-disable-line no-silent

        // Pass in filter settings
        pageDetails.filter = self.getFilterAstTree();
        var imagesDeferred = $.Deferred();
        var images = new isic.collections.ImageCollection();
        images.once('g:changed', _.bind(function () {
            this.set('imageIds', images.pluck('_id'));
            imagesDeferred.resolve();
        }, this)).fetch({
            limit: pageDetails.limit,
            offset: pageDetails.offset,
            filter: self.getFilterAstTree()
        });

        var histogramRequest = self.updateHistogram('page');
        return $.when(imagesDeferred.promise(), histogramRequest);
    },
    getPageDetails: function (capLimit) {
        var self = this;
        var result = {
            overviewCount: self.get('overviewHistogram').__passedFilters__[0].count,
            filteredSetCount: self.get('filteredSetHistogram').__passedFilters__[0].count,
            offset: self.get('offset'),
            limit: self.get('limit')
        };
        if (capLimit && result.offset + result.limit > result.filteredSetCount) {
            result.limit = result.filteredSetCount - result.offset;
        }
        return result;
    },
    postProcessHistogram: function (histogram) {
        var self = this;
        var formatter = d3.format('0.3s');
        _.each(histogram, function (value, key) {
            _.each(value, function (bin, index) {
                if (key === 'folderId') {
                    bin.label = self.datasetCollection.get(bin.label).name();
                } else if (_.isNumber(bin.lowBound) &&
                        _.isNumber(bin.highBound)) {
                    // binUtils.js doesn't have access to D3's superior number
                    // formatting abilities, so we patch on slightly better
                    // human-readable labels
                    bin.label = '[' + formatter(bin.lowBound) + ' - ' +
                        formatter(bin.highBound);
                    if (index === value.length - 1) {
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
        var attrSpec = window.ENUMS.SCHEMA[attrName];
        // Find the most specific type that can accomodate all the values
        var attrType = 'object';
        var count = 0;
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
                };
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

        // Even though the object internals change,
        // Backbone sometimes won't fire the change:filter
        // event (because the object reference matches).
        // Instead, we silently set the filter (so there
        // aren't two events), and trigger the event manually
        self.set('filter', filter, {silent: true}); // eslint-disable-line no-silent
        self.trigger('change:filter');
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
        var self = this;
        var filter = self.get('filter');
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
    },
    listCategoricalFilterExpressions: function (attrName, filterSpec, hexify) {
        hexify = !!hexify;
        var self = this;
        var values;
        var operation;
        if (filterSpec.hasOwnProperty('includeValues')) {
            values = filterSpec.includeValues;
            operation = ' in ';
        } else if (filterSpec.hasOwnProperty('excludeValues')) {
            values = filterSpec.excludeValues;
            operation = ' not in ';
        } else {
            return [];
        }
        if (hexify) {
            attrName = self.stringToHex(attrName);
            var temp = values;
            values = [];
            temp.forEach(function (value) {
                var dataType = typeof value;
                if (dataType === 'string' || dataType === 'object') {
                    value = self.stringToHex(value);
                }
                values.push(value);
            });
        }
        return [attrName + operation + JSON.stringify(values)];
    },
    listRangeFilterExpressions: function (attrName, filterSpec, hexify) {
        hexify = !!hexify;
        var self = this;
        var results = [];
        if (filterSpec.excludeRanges) {
            var temp = '(';
            var firstRange = true;
            if (hexify) {
                attrName = self.stringToHex(attrName);
            }
            filterSpec.excludeRanges.forEach(function (range) {
                if (!firstRange) {
                    temp += ' and ';
                }
                firstRange = false;
                temp += '(';
                var includeLow = false;
                var dataType;
                if (range.hasOwnProperty('lowBound')) {
                    var lowBound = range.lowBound;
                    dataType = typeof lowBound;
                    if (dataType === 'string' || dataType === 'object') {
                        if (hexify) {
                            lowBound = self.stringToHex(String(lowBound));
                        }
                        lowBound = '"' + lowBound + '"';
                    }
                    temp += attrName + ' < ' + lowBound;
                    includeLow = true;
                }
                if (range.hasOwnProperty('highBound')) {
                    if (includeLow) {
                        temp += ' or ';
                    }
                    var highBound = range.highBound;
                    dataType = typeof highBound;
                    if (dataType === 'string' || dataType === 'object') {
                        if (hexify) {
                            highBound = self.stringToHex(String(highBound));
                        }
                        highBound = '"' + highBound + '"';
                    }
                    temp += attrName + ' >= ' + highBound;
                }
                temp += ')';
            });
            temp += ')';
            results.push(temp);
        }
        return results;
    },
    listStandardFilterExpressions: function (hexify) {
        hexify = !!hexify;
        var self = this;
        var filter = self.get('filter');
        var results = [];
        Object.keys(filter.standard).forEach(function (attrName) {
            var filterSpec = filter.standard[attrName];
            results = results.concat(self.listCategoricalFilterExpressions(attrName, filterSpec, hexify));
            results = results.concat(self.listRangeFilterExpressions(attrName, filterSpec, hexify));
        });
        return results;
    },
    listAllFilterExpressions: function (hexify) {
        hexify = !!hexify;
        var self = this;
        var filter = self.get('filter');
        var exprList = self.listStandardFilterExpressions(hexify);
        exprList = exprList.concat(filter.custom);
        return exprList;
    },
    stringToHex: function (value) {
        var result = '';
        for (var i = 0; i < value.length; i += 1) {
            result += '%' + value.charCodeAt(i).toString(16);
        }
        return result;
    },
    dehexify: function (obj) {
        var self = this;
        if (!obj) {
            return obj;
        }
        if (_.isObject(obj)) {
            if (_.isArray(obj)) {
                obj.forEach(function (d, i) {
                    obj[i] = self.dehexify(d);
                });
            } else {
                Object.keys(obj).forEach(function (k) {
                    obj[k] = self.dehexify(obj[k]);
                });
            }
        } else if (_.isString(obj)) {
            obj = decodeURIComponent(obj);
        }
        return obj;
    },
    specifyAttrTypes: function (obj) {
        var self = this;
        if (!_.isObject(obj)) {
            return obj;
        } else if ('identifier' in obj && 'type' in obj && obj.type === null) {
            var attrType = self.getAttributeType(obj.identifier);
            if (attrType !== 'object') {
                // 'object' is really a passthrough; don't attempt
                // any coercion while performing the filter
                obj.type = attrType;
            }
        } else if (_.isArray(obj)) {
            obj.forEach(function (d, i) {
                obj[i] = self.specifyAttrTypes(d);
            });
        } else {
            Object.keys(obj).forEach(function (k) {
                obj[k] = self.specifyAttrTypes(obj[k]);
            });
        }
        return obj;
    },
    getFilterAstTree: function () {
        var self = this;
        var exprList = self.listAllFilterExpressions(true);

        if (exprList.length > 0) {
            var fullExpression = '(' + exprList.join(') and (') + ')';
            var ast = self.astParser.parse(fullExpression);
            ast = self.dehexify(ast);
            return self.specifyAttrTypes(ast);
        } else {
            return undefined;
        }
    }
});

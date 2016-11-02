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
        overviewHistogram: {
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
        }
    },
    initialize: function () {
        this.datasetCollection = new isic.collections.DatasetCollection();
        this.images = new isic.collections.ImageCollection();
        this.images.pageLimit = 50;

        // Load the pegjs grammar and fetch the datasets
        // before attempting to get histograms or image IDs
        $.when(this.fetchDatasets(), this.loadFilterGrammar())
            .then(_.bind(function () {
                // We need the dataset names before getting any histograms
                this.updateOverviewHistogram();
                // We need the dataset names and the filter grammar before getting
                // the filtered set or the current page (both the page of images
                // and the page histogram)
                this.updateFilters();
            }, this));

        this.listenTo(this, 'change:limit', this.updateCurrentPage);
        this.listenTo(this, 'change:offset', this.updateCurrentPage);
        this.listenTo(this, 'change:filter', this.updateFilters);
    },
    fetchDatasets: function () {
        var deferred = $.Deferred();
        this.datasetCollection.once('g:changed', function () {
            deferred.resolve();
        }).fetch({
            limit: 0
        });
        return deferred.promise();
    },
    loadFilterGrammar: function () {
        return $.ajax({
            url: girder.staticRoot + '/built/plugins/isic_archive/extra/query.pegjs',
            dataType: 'text',
            success: _.bind(function (data) {
                this.astParser = peg.generate(data);
            }, this)
        });
    },
    updateOverviewHistogram: function () {
        return girder.restRequest({
            path: 'image/histogram'
        }).then(_.bind(function (resp) {
            var histogram = this.postProcessHistogram(resp);
            this.set('overviewHistogram', histogram);
        }, this));
    },
    updateFilteredSetHistogram: function () {
        return girder.restRequest({
            path: 'image/histogram',
            data: {
                filter: JSON.stringify(this.getFilterAstTree())
            }
        }).then(_.bind(function (resp) {
            var histogram = this.postProcessHistogram(resp);
            this.set('filteredSetHistogram', histogram);
        }, this));
    },
    updateFilters: function () {
        return $.when(
            this.updateFilteredSetHistogram(),
            this.updateCurrentPage()
        );
    },
    updateCurrentPage: function () {
        // Construct the parameters to send to the server
        var pageDetails = this.getPageDetails();

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
        this.set({
            limit: pageDetails.limit,
            offset: pageDetails.offset
        }, {silent: true}); // eslint-disable-line backbone/no-silent

        // Pass in filter settings
        pageDetails.filter = this.getFilterAstTree();
        var imagesDeferred = $.Deferred();

        // upstream Girder contains a bug where parameters are not honored on a
        // reset fetch, so set the parameters manually before triggering a fetch
        // with (ignored) params set to null, and the reset flag set to true.
        this.images.params = {
            offset: pageDetails.offset,
            filter: JSON.stringify(this.getFilterAstTree())
        };
        this.images.once('g:changed', _.bind(function () {
            imagesDeferred.resolve();
        }, this)).fetch(null, true);

        return imagesDeferred.promise();
    },
    getPageDetails: function (capLimit) {
        var result = {
            overviewCount: this.get('overviewHistogram').__passedFilters__[0].count,
            filteredSetCount: this.get('filteredSetHistogram').__passedFilters__[0].count,
            offset: this.get('offset'),
            limit: this.get('limit')
        };
        if (capLimit && result.offset + result.limit > result.filteredSetCount) {
            result.limit = result.filteredSetCount - result.offset;
        }
        return result;
    },
    postProcessHistogram: function (histogram) {
        var formatter = d3.format('0.3s');
        _.each(histogram, _.bind(function (value, key) {
            _.each(value, _.bind(function (bin, index) {
                if (key === 'folderId') {
                    bin.label = this.datasetCollection.get(bin.label).name();
                } else if (_.isNumber(bin.lowBound) && _.isNumber(bin.highBound)) {
                    // binUtils.js doesn't have access to D3's superior number
                    // formatting abilities, so we patch on slightly better
                    // human-readable labels
                    bin.label = bin.label[0] + formatter(bin.lowBound) + ' - ' +
                        formatter(bin.highBound) + bin.label[bin.label.length - 1];
                 }
            }, this));
        }, this));
        return histogram;
    },
    autoDetectAttributeInterpretation: function (attrName) {
        // Go with the default interpretation for the attribute type
        return isic.ENUMS.DEFAULT_INTERPRETATIONS[this.getAttributeType(attrName)];
    },
    getAttributeInterpretation: function (attrName) {
        var attrSpec = isic.ENUMS.SCHEMA[attrName];
        if (attrSpec.interpretation) {
            // The user has specified an interpretation
            return attrSpec.interpretation;
        } else {
            // auto-detect the interpretation
            return this.autoDetectAttributeInterpretation(attrName);
        }
    },
    autoDetectAttributeType: function (attrName) {
        var attrSpec = isic.ENUMS.SCHEMA[attrName];
        // Find the most specific type that can accomodate all the values
        var attrType = 'object';
        var count = 0;
        _.each(isic.ENUMS.ATTRIBUTE_GENERALITY, function (dataType) {
            if (_.has(attrSpec, dataType) &&
                  attrSpec[dataType].count >= count) {
                attrType = dataType;
                count = attrSpec[dataType].count;
            }
        });
        return attrType;
    },
    getAttributeType: function (attrName) {
        var attrSpec = isic.ENUMS.SCHEMA[attrName];
        if (attrSpec.coerceToType) {
            // The user has specified a data type
            return attrSpec.coerceToType;
        } else {
            // auto-detect the data type
            return this.autoDetectAttributeType(attrName);
        }
    },
    getBinStatus: function (attrName, bin) {
        // Easy check (that also validates whether filter.standard[attrName]
        // even exists)
        var filterState = this.getFilteredState(attrName);
        if (filterState === isic.ENUMS.FILTER_STATES.NO_FILTERS) {
            return isic.ENUMS.BIN_STATES.INCLUDED;
        }

        var filterSpec = this.get('filter').standard[attrName];

        // Next easiest check: is the label not in the include list (if there is
        // one) / in the list that is specifically excluded?
        if (filterSpec.includeValues &&
                filterSpec.includeValues.indexOf(bin.label) === -1) {
            return isic.ENUMS.BIN_STATES.EXCLUDED;
        } else if (filterSpec.excludeValues &&
                filterSpec.excludeValues.indexOf(bin.label) !== -1) {
            return isic.ENUMS.BIN_STATES.EXCLUDED;
        }

        // Trickiest check: is the range excluded (or partially excluded)?
        if (filterSpec.excludeRanges &&
                _.has(bin, 'lowBound') &&
                _.has(bin, 'highBound')) {
            // Make sure to use proper string comparisons if this is a string bin
            var comparator;
            if (this.getAttributeType(attrName) === 'string') {
                comparator = function (a, b) {
                    return a.localeCompare(b);
                };
            }
            // Intersect the bin with the excluded values
            var includedRanges = isic.shims.RangeSet.rangeSubtract([{
                lowBound: bin.lowBound,
                highBound: bin.highBound
            }], filterSpec.excludeRanges, comparator);

            if (includedRanges.length === 1 &&
                    includedRanges[0].lowBound === bin.lowBound &&
                    includedRanges[0].highBound === bin.highBound) {
                // Wound up with the same range we started with;
                // the whole bin is included
                return isic.ENUMS.BIN_STATES.INCLUDED;
            } else if (includedRanges.length > 0) {
                // Only a piece survived; this is a partial!
                return isic.ENUMS.BIN_STATES.PARTIAL;
            } else {
                // Nothing survived the subtraction; this bin
                // is excluded
                return isic.ENUMS.BIN_STATES.EXCLUDED;
            }
        }

        // No filter info left to check; the bin must be included
        return isic.ENUMS.BIN_STATES.INCLUDED;
    },
    applyFilter: function (filter) {
        // Clean up the filter specification
        var standardKeys = Object.keys(filter.standard);
        _.each(standardKeys, function (k) {
            var removeFilterSpec = !_.has(filter.standard[k], 'excludeAttribute');
            _.each(['excludeRanges', 'includeValues', 'excludeValues'], function (d) {
                if (_.has(filter.standard[k], d)) {
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
        this.set('filter', filter, {silent: true}); // eslint-disable-line backbone/no-silent
        this.trigger('change:filter');
    },
    clearFilters: function (attrName) {
        var filter = this.get('filter');
        if (_.has(filter.standard, attrName)) {
            delete filter.standard[attrName].excludeRanges;
            delete filter.standard[attrName].excludeValues;
            delete filter.standard[attrName].includeValues;
            this.applyFilter(filter);
        }
    },
    selectRange: function (attrName, lowBound, highBound) {
        var filter = this.get('filter');
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

        this.applyFilter(filter);
    },
    removeRange: function (attrName, lowBound, highBound, comparator) {
        var filter = this.get('filter');
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
        excludeRanges = isic.shims.RangeSet.rangeUnion(
            excludeRanges, [range], comparator);
        filter.standard[attrName].excludeRanges = excludeRanges;

        this.applyFilter(filter);
    },
    includeRange: function (attrName, lowBound, highBound, comparator) {
        var filter = this.get('filter');
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
        excludeRanges = isic.shims.RangeSet.rangeSubtract(
            excludeRanges, [range], comparator);
        filter.standard[attrName].excludeRanges = excludeRanges;

        this.applyFilter(filter);
    },
    selectValues: function (attrName, values) {
        var filter = this.get('filter');
        // Temporarily init a filter object for this attribute
        // if it doesn't already exist
        if (!filter.standard[attrName]) {
            filter.standard[attrName] = {};
        }

        // Select ONLY the given values
        filter.standard[attrName].includeValues = values;
        delete filter.standard[attrName].excludeValues;

        this.applyFilter(filter);
    },
    removeValue: function (attrName, value) {
        var filter = this.get('filter');
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

        this.applyFilter(filter);
    },
    includeValue: function (attrName, value) {
        var filter = this.get('filter');
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

        this.applyFilter(filter);
    },
    getFilteredState: function (attrName) {
        var filter = this.get('filter');
        if (filter.standard[attrName]) {
            if (filter.standard[attrName].excludeAttribute) {
                return isic.ENUMS.FILTER_STATES.EXCLUDED;
            } else {
                return isic.ENUMS.FILTER_STATES.FILTERED;
            }
        } else {
            return isic.ENUMS.FILTER_STATES.NO_FILTERS;
        }
    },
    listCategoricalFilterExpressions: function (attrName, filterSpec, hexify) {
        hexify = !!hexify;
        var values;
        var operation;
        if (_.has(filterSpec, 'includeValues')) {
            values = filterSpec.includeValues;
            operation = ' in ';
        } else if (_.has(filterSpec, 'excludeValues')) {
            values = filterSpec.excludeValues;
            operation = ' not in ';
        } else {
            return [];
        }
        if (hexify) {
            attrName = this.stringToHex(attrName);
            var temp = values;
            values = [];
            _.each(temp, function (value) {
                var dataType = typeof value;
                if (dataType === 'string' || dataType === 'object') {
                    value = this.stringToHex(value);
                }
                values.push(value);
            }, this);
        }
        return [attrName + operation + JSON.stringify(values)];
    },
    listRangeFilterExpressions: function (attrName, filterSpec, hexify) {
        hexify = !!hexify;
        var results = [];
        if (filterSpec.excludeRanges) {
            var temp = '(';
            var firstRange = true;
            if (hexify) {
                attrName = this.stringToHex(attrName);
            }
            _.each(filterSpec.excludeRanges, function (range) {
                if (!firstRange) {
                    temp += ' and ';
                }
                firstRange = false;
                temp += '(';
                var includeLow = false;
                var dataType;
                if (_.has(range, 'lowBound')) {
                    var lowBound = range.lowBound;
                    dataType = typeof lowBound;
                    if (dataType === 'string' || dataType === 'object') {
                        if (hexify) {
                            lowBound = this.stringToHex(String(lowBound));
                        }
                        lowBound = '"' + lowBound + '"';
                    }
                    temp += 'not (' + attrName + ' >= ' + lowBound + ')';
                    includeLow = true;
                }
                if (_.has(range, 'highBound')) {
                    if (includeLow) {
                        temp += ' or ';
                    }
                    var highBound = range.highBound;
                    dataType = typeof highBound;
                    if (dataType === 'string' || dataType === 'object') {
                        if (hexify) {
                            highBound = this.stringToHex(String(highBound));
                        }
                        highBound = '"' + highBound + '"';
                    }
                    temp += 'not (' + attrName + ' < ' + highBound + ')';
                }
                temp += ')';
            }, this);
            temp += ')';
            results.push(temp);
        }
        return results;
    },
    listStandardFilterExpressions: function (hexify) {
        hexify = !!hexify;
        var filter = this.get('filter');
        var results = [];
        _.each(Object.keys(filter.standard), function (attrName) {
            var filterSpec = filter.standard[attrName];
            results = results.concat(this.listCategoricalFilterExpressions(attrName, filterSpec, hexify));
            results = results.concat(this.listRangeFilterExpressions(attrName, filterSpec, hexify));
        }, this);
        return results;
    },
    listAllFilterExpressions: function (hexify) {
        hexify = !!hexify;
        var filter = this.get('filter');
        var exprList = this.listStandardFilterExpressions(hexify);
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
        if (!obj) {
            return obj;
        }
        if (_.isObject(obj)) {
            if (_.isArray(obj)) {
                _.each(obj, function (d, i) {
                    obj[i] = this.dehexify(d);
                }, this);
            } else {
                _.each(Object.keys(obj), function (k) {
                    obj[k] = this.dehexify(obj[k]);
                }, this);
            }
        } else if (_.isString(obj)) {
            obj = decodeURIComponent(obj);
        }
        return obj;
    },
    specifyAttrTypes: function (obj) {
        if (!_.isObject(obj)) {
            return obj;
        } else if ('identifier' in obj && 'type' in obj && obj.type === null) {
            var attrType = this.getAttributeType(obj.identifier);
            if (attrType !== 'object') {
                // 'object' is really a passthrough; don't attempt
                // any coercion while performing the filter
                obj.type = attrType;
            }
        } else if (_.isArray(obj)) {
            _.each(obj, function (d, i) {
                obj[i] = this.specifyAttrTypes(d);
            }, this);
        } else {
            _.each(Object.keys(obj), function (k) {
                obj[k] = this.specifyAttrTypes(obj[k]);
            }, this);
        }
        return obj;
    },
    getFilterAstTree: function () {
        var exprList = this.listAllFilterExpressions(true);

        if (exprList.length > 0) {
            var fullExpression = '(' + exprList.join(') and (') + ')';
            var ast = this.astParser.parse(fullExpression);
            ast = this.dehexify(ast);
            return this.specifyAttrTypes(ast);
        } else {
            return undefined;
        }
    }
});

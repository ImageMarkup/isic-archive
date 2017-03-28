/*globals peg*/

isic.collections.ImagesFilters = function (completeFacets) {
    if (completeFacets) {
        this.initialize(completeFacets);
    }
};
_.extend(isic.collections.ImagesFilters.prototype, Backbone.Events, {
    initialize: function (completeFacets) {
        /* Creates an internal structure of:
            this._filters = {
                facetId1: {
                    binLabel1: true,
                    binLabel2: false,
                    ...
                },
                facetId2: {
                    binLabel1: true,
                    binLabel2: false,
                    ...
                },
                ...
            }
        */
        this._filters = completeFacets.chain()
            .map(function (completeFacet) {
                var facetId = completeFacet.id;
                var facetBins = completeFacet.get('bins');

                var facetFilters = _.chain(facetBins)
                    .map(function (facetBin) {
                        var binLabel = facetBin.label;
                        // Default to all bins included
                        var binIncluded = true;
                        return [binLabel, binIncluded];
                    })
                    .object()
                    .value();

                return [facetId, facetFilters];
            })
            .object()
            .value();
    },

    isIncluded: function (facetId, binLabel) {
        return this._filters[facetId][binLabel];
    },

    setIncluded: function (facetId, binLabel, binIncluded) {
        this._filters[facetId][binLabel] = binIncluded;
        this.trigger('change:' + facetId);
        this.trigger('change');
    },

    setAllIncluded: function (facetId, binsIncluded) {
        _.each(this._filters[facetId], function (oldValue, binLabel, facetBin) {
            facetBin[binLabel] = binsIncluded;
        });
        this.trigger('change:' + facetId);
        this.trigger('change');
    },

    asAst: function () {
        var fullExpression = _.chain(this._filters)
            .pick(function (facetFilters, facetId) {
                // Keep (facetId: facetFilter) elements that have at least one excluded bin
                return _.chain(facetFilters)
                    .values()
                    .contains(false)
                    .value();
            })
            .map(function (facetFilters, facetId) {
                // Convert each facet into a string filter expression
                if (_.has(isic.FACET_SCHEMA[facetId], 'lowBound')) {
                    return this._rangeFacetFilterExpression(facetId, facetFilters);
                } else {
                    return this._categoricalFacetFilterExpression(facetId, facetFilters);
                }
            }, this)
            .value()
            .join(' and ');
        if (fullExpression) {
            var ast = isic.SerializeFilterHelpers.astParser.parse(fullExpression);
            ast = isic.SerializeFilterHelpers._dehexify(ast);
            // TODO: "__null__" values in range facets get their type set as "number" here
            return isic.SerializeFilterHelpers._specifyAttrTypes(ast);
        } else {
            return undefined;
        }
    },

    _rangeFacetFilterExpression: function (facetId, facetFilters) {
        var filterExpressions = _.chain(facetFilters)
            .pick(function (binIncluded, binLabel) {
                // Because '__null__' has no high or low bound, it must be handled specially
                return binIncluded === false && binLabel !== '__null__';
            })
            .map(function (binIncluded, binLabel) {
                // Parse range labels, to yield an array of numeric range arrays
                var rangeMatches = binLabel.match(/\[([\d.]+) - ([\d.]+)\)/);
                var lowBound = parseFloat(rangeMatches[1]);
                var highBound = parseFloat(rangeMatches[2]);
                return [lowBound, highBound];
            })
            .sortBy(_.identity)
            .reduce(function (allRanges, curRange) {
                // Combine adjacent ranges
                var prevRange = _.last(allRanges);
                // Compare the previous high bound and the current low bound, checking for
                // the special case of the first element where there's no "prevRange"
                if (prevRange && prevRange[1] === curRange[0]) {
                    // If they match, combine the current high bound with the previous low
                    // bound
                    var combinedRange = [prevRange[0], curRange[1]];
                    // Pop the previous range, and add the combined range
                    return allRanges.slice(0, -1).concat([combinedRange]);
                } else {
                    // If there's no match, just push the current range onto the list
                    return allRanges.concat([curRange]);
                }
            }, [])
            .map(function (range) {
                // Convert each range into a string expression
                var lowBoundExpression = 'not (' +
                    isic.SerializeFilterHelpers._stringToHex(facetId) +
                    ' >= ' +
                    range[0] +
                    ')';
                var highBoundExpression = 'not (' +
                    isic.SerializeFilterHelpers._stringToHex(facetId) +
                    ' < ' +
                    range[1] +
                    ')';
                return '(' + lowBoundExpression + ' or ' + highBoundExpression + ')';
            })
            .value();
        if (facetFilters['__null__'] === false) {
            // This conditional will also intentionally fail if '__null__' is undefined
            filterExpressions.push(this._categoricalFacetFilterExpression(
                facetId, _.pick(facetFilters, '__null__')));
        }
        // Combine all expressions
        return '(' + filterExpressions.join(' and ') + ')';
    },

    _categoricalFacetFilterExpression: function (facetId, facetFilters) {
        var excludedBinLabels = _.chain(facetFilters)
            .pick(function (binIncluded, binLabel) {
                return binIncluded === false;
            })
            .keys()
            // Each of these must be encoded, as they're user-provided values from the database
            .map(isic.SerializeFilterHelpers._stringToHex)
            .value();
        // TODO: Could use "facetId + ' in ' + includedBinLabels"" if most are excluded
        return '(' +
            // TODO: This doesn't strictly need to be encoded (provided that we don't use any of the
            // grammar's forbidden characters for identifiers), but before removing the encoding
            // step, we should ensure that decoding it (which always happens) will be a safe no-op
            isic.SerializeFilterHelpers._stringToHex(facetId) +
            ' not in ' +
            JSON.stringify(excludedBinLabels) +
            ')';
    }
});

isic.SerializeFilterHelpers = {
    loadFilterGrammar: function () {
        // TODO: inline this as a string literal
        return $.ajax({
            url: girder.staticRoot + '/built/plugins/isic_archive/extra/query.pegjs',
            dataType: 'text',
            success: _.bind(function (data) {
                isic.SerializeFilterHelpers.astParser = peg.generate(data);
            }, this)
        });
    },

    _stringToHex: function (value) {
        var result = '';
        for (var i = 0; i < value.length; i += 1) {
            result += '%' + value.charCodeAt(i).toString(16);
        }
        return result;
    },

    _dehexify: function (obj) {
        if (!obj) {
            return obj;
        }
        if (_.isObject(obj)) {
            if (_.isArray(obj)) {
                _.each(obj, function (d, i) {
                    obj[i] = isic.SerializeFilterHelpers._dehexify(d);
                });
            } else {
                _.each(Object.keys(obj), function (k) {
                    obj[k] = isic.SerializeFilterHelpers._dehexify(obj[k]);
                });
            }
        } else if (_.isString(obj)) {
            obj = decodeURIComponent(obj);
        }
        return obj;
    },

    _specifyAttrTypes: function (obj) {
        if (!_.isObject(obj)) {
            return obj;
        } else if ('identifier' in obj && 'type' in obj && obj.type === null) {
            var attrType = isic.FACET_SCHEMA[obj.identifier].coerceToType;
            if (attrType !== 'object') {
                // 'object' is really a passthrough; don't attempt
                // any coercion while performing the filter
                obj.type = attrType;
            }
        } else if (_.isArray(obj)) {
            _.each(obj, function (d, i) {
                obj[i] = isic.SerializeFilterHelpers._specifyAttrTypes(d);
            });
        } else {
            _.each(Object.keys(obj), function (k) {
                obj[k] = isic.SerializeFilterHelpers._specifyAttrTypes(obj[k]);
            });
        }
        return obj;
    }
};

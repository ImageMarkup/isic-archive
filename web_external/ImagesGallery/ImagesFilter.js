import Backbone from 'backbone';
import peg from 'pegjs';
import _ from 'underscore';

import {FACET_SCHEMA} from './Facets/ImagesFacetView';
import queryGrammar from 'raw-loader!./query.pegjs';

var ImagesFilter = function (completeFacets) {
    this.astParser = peg.generate(queryGrammar);

    if (completeFacets) {
        this.initialize(completeFacets);
    }
};
_.extend(ImagesFilter.prototype, Backbone.Events, {
    initialize: function (completeFacets) {
        /* Creates an internal structure of:
            this._filters = {
                facetId1: FacetFilter,
                facetId2: FacetFilter,
                ...
            }
        */
        this._filters = {};
        completeFacets.forEach(_.bind(function (completeFacet) {
            var facetId = completeFacet.id;
            var FacetFilter = FACET_SCHEMA[facetId].FacetFilter;
            var facetFilter = new FacetFilter(facetId, completeFacet.get('bins'));
            facetFilter.on('change', function () {
                // Trigger a change on the parent whenever a child changes
                this.trigger('change');
            }, this);
            this._filters[facetId] = facetFilter;
        }, this));
    },

    facetFilter: function (facetId) {
        return this._filters[facetId];
    },

    asExpression: function () {
        return _.chain(this._filters)
            .invoke('asExpression')
            // Remove empty expressions
            .compact()
            .value()
            .join(' and ');
    },

    asAst: function () {
        var fullExpression = this.asExpression();
        if (fullExpression) {
            var ast = this.astParser.parse(fullExpression);
            ast = SerializeFilterHelpers._dehexify(ast);
            // TODO: "__null__" values in range facets get their type set as "number" here
            return SerializeFilterHelpers._specifyAttrTypes(ast);
        } else {
            return undefined;
        }
    }
});

var FacetFilter = function (facetId, facetBins) {
    this.facetId = facetId;

    /* Creates an internal structure of:
        this._filters = {
            binLabel1: true,
            binLabel2: true,
            ...
        }
    */
    this._filters = {};
    _.each(facetBins, _.bind(function (facetBin) {
        // Default to all bins included
        this._filters[facetBin.label] = true;
    }, this));
};

// Make it easy to inherit from FacetFilter, using a utility function from Backbone
FacetFilter.extend = Backbone.View.extend;

_.extend(FacetFilter.prototype, Backbone.Events, {
    isIncluded: function (binLabel) {
        return this._filters[binLabel];
    },

    setIncluded: function (binLabel, binIncluded) {
        this._filters[binLabel] = binIncluded;
        this.trigger('change');
    },

    setAllIncluded: function (binsIncluded) {
        _.each(this._filters, _.bind(function (oldValue, binLabel) {
            this._filters[binLabel] = binsIncluded;
        }, this));
        this.trigger('change');
    },

    asExpression: null
});

var CategoricalFacetFilter = FacetFilter.extend({
    asExpression: function () {
        var excludedBinLabels = _.chain(this._filters)
            // Choose only excluded bins
            .pick(function (binIncluded, binLabel) {
                return binIncluded === false;
            })
            // Take the bin labels as an array
            .keys()
            // Encode each, as they're user-provided values from the database
            .map(SerializeFilterHelpers._stringToHex)
            .value();
        // TODO: Could use "facetId + ' in ' + includedBinLabels"" if most are excluded
        if (_.size(excludedBinLabels) === 0) {
            // If none are excluded, return no filter
            return '';
        } else {
            return '(' +
                // TODO: This doesn't strictly need to be encoded (provided that we don't use any of
                // the grammar's forbidden characters for identifiers), but before removing the
                // encoding step, we should ensure that decoding it (which always happens) will be a
                // safe no-op
                SerializeFilterHelpers._stringToHex(this.facetId) +
                ' not in ' +
                JSON.stringify(excludedBinLabels) +
                ')';
        }
    }
});

var TagsCategoricalFacetFilter = CategoricalFacetFilter.extend({
    asExpression: function () {
        var includedBinLabels = _.chain(this._filters)
            // Choose only included bins
            .pick(function (binIncluded, binLabel) {
                return binIncluded === true;
            })
            // Take the bin labels as an array
            .keys()
            // Encode each, as they're user-provided values from the database
            .map(function (binLabel) {
                if (binLabel === '__null__') {
                    // The null bin matches an empty array (with no tags) in the database
                    // Non-strings can't be encoded, so don't encode this value
                    return [];
                }
                return SerializeFilterHelpers._stringToHex(binLabel);
            })
            .value();
        if (_.size(includedBinLabels) === _.size(this._filters)) {
            // If all are included, return no filter
            return '';
        } else {
            return '(' +
                SerializeFilterHelpers._stringToHex(this.facetId) +
                ' in ' +
                JSON.stringify(includedBinLabels) +
                ')';
        }
    }
});

var IntervalFacetFilter = FacetFilter.extend({
    asExpression: function () {
        var filterExpressions = _.chain(this._filters)
            // Because '__null__' has no high or low bound, it must be handled specially
            .pick(function (binIncluded, binLabel) {
                return binIncluded === false && binLabel !== '__null__';
            })
            // Parse range labels, to yield an array of numeric range arrays
            .map(function (binIncluded, binLabel) {
                var rangeMatches = binLabel.match(/\[([\d.]+) - ([\d.]+)\)/);
                var lowBound = parseFloat(rangeMatches[1]);
                var highBound = parseFloat(rangeMatches[2]);
                return [lowBound, highBound];
            })
            .sortBy(_.identity)
            // Combine adjacent ranges
            .reduce(function (allRanges, curRange) {
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
            // Convert each range into a string expression
            .map(_.bind(function (range) {
                var lowBoundExpression = 'not (' +
                    SerializeFilterHelpers._stringToHex(this.facetId) +
                    ' >= ' +
                    range[0] +
                    ')';
                var highBoundExpression = 'not (' +
                    SerializeFilterHelpers._stringToHex(this.facetId) +
                    ' < ' +
                    range[1] +
                    ')';
                return '(' + lowBoundExpression + ' or ' + highBoundExpression + ')';
            }, this))
            .value();
        if (this._filters['__null__'] === false) {
            // This conditional will also intentionally fail if '__null__' is undefined
            filterExpressions.push(
                '(' +
                SerializeFilterHelpers._stringToHex(this.facetId) +
                ' not in ' +
                JSON.stringify([SerializeFilterHelpers._stringToHex('__null__')]) +
                ')'
            );
        }
        if (_.size(filterExpressions) === 0) {
            // If none are excluded, return no filter
            return '';
        } else {
            // Combine all expressions
            return '(' + filterExpressions.join(' and ') + ')';
        }
    }
});

var SerializeFilterHelpers = {
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
                    obj[i] = SerializeFilterHelpers._dehexify(d);
                });
            } else {
                _.each(Object.keys(obj), function (k) {
                    obj[k] = SerializeFilterHelpers._dehexify(obj[k]);
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
            var attrType = FACET_SCHEMA[obj.identifier].coerceToType;
            if (attrType !== 'object') {
                // 'object' is really a passthrough; don't attempt
                // any coercion while performing the filter
                obj.type = attrType;
            }
        } else if (_.isArray(obj)) {
            _.each(obj, function (d, i) {
                obj[i] = SerializeFilterHelpers._specifyAttrTypes(d);
            });
        } else {
            _.each(Object.keys(obj), function (k) {
                obj[k] = SerializeFilterHelpers._specifyAttrTypes(obj[k]);
            });
        }
        return obj;
    }
};

export default ImagesFilter;
export {CategoricalFacetFilter, IntervalFacetFilter, TagsCategoricalFacetFilter};

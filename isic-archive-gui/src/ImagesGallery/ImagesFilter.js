import Backbone from 'backbone';
import _ from 'underscore';

import {FACET_SCHEMA} from './Facets/ImagesFacetView';
import queryParser from './query.pegjs';

const ImagesFilter = function (completeFacets) {
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
        completeFacets.forEach((completeFacet) => {
            let facetId = completeFacet.id;
            let FacetFilter = FACET_SCHEMA[facetId].FacetFilter;
            let facetFilter = new FacetFilter(facetId, completeFacet.get('bins'));
            facetFilter.on('change', () => {
                // Trigger a change on the parent whenever a child changes
                this.trigger('change');
            });
            this._filters[facetId] = facetFilter;
        });
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
        let fullExpression = this.asExpression();
        if (fullExpression) {
            let ast = queryParser.parse(fullExpression);
            ast = SerializeFilterHelpers._dehexify(ast);
            // TODO: "__null__" values in range facets get their type set as "number" here
            return SerializeFilterHelpers._specifyAttrTypes(ast);
        } else {
            return undefined;
        }
    }
});

const FacetFilter = function (facetId, facetBins) {
    this.facetId = facetId;

    /* Creates an internal structure of:
        this._filters = {
            binLabel1: true,
            binLabel2: true,
            ...
        }
    */
    this._filters = {};
    _.each(facetBins, (facetBin) => {
        // Default to all bins included
        this._filters[facetBin.label] = true;
    });
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
        _.each(this._filters, (oldValue, binLabel) => {
            this._filters[binLabel] = binsIncluded;
        });
        this.trigger('change');
    },

    asExpression: null
});

const CategoricalFacetFilter = FacetFilter.extend({
    asExpression: function () {
        let excludedBinLabels = _.chain(this._filters)
            // Choose only excluded bins
            .pick((binIncluded, binLabel) => {
                return binIncluded === false;
            })
            // Take the bin labels as an array
            .keys()
            // Encode each, as they're user-provided values from the database
            .map(SerializeFilterHelpers._stringToHex)
            .value();
        // TODO: Could use `(${hexFacetId} not in ${jsonIncludedBinLabels})` if most are excluded
        if (_.size(excludedBinLabels) === 0) {
            // If none are excluded, return no filter
            return '';
        } else {
            // TODO: hexFacetId doesn't strictly need to be encoded (provided that we don't use any
            // of the grammar's forbidden characters for identifiers), but before removing the
            // encoding step, we should ensure that decoding it (which always happens) will be a
            // safe no-op
            let hexFacetId = SerializeFilterHelpers._stringToHex(this.facetId);
            let jsonExcludedBinLabels = JSON.stringify(excludedBinLabels);
            return `(${hexFacetId} not in ${jsonExcludedBinLabels})`;
        }
    }
});

const TagsCategoricalFacetFilter = CategoricalFacetFilter.extend({
    asExpression: function () {
        let includedBinLabels = _.chain(this._filters)
            // Choose only included bins
            .pick((binIncluded, binLabel) => {
                return binIncluded === true;
            })
            // Take the bin labels as an array
            .keys()
            // Encode each, as they're user-provided values from the database
            .map((binLabel) => {
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
            let hexFacetId = SerializeFilterHelpers._stringToHex(this.facetId);
            let jsonIncludedBinLabels = JSON.stringify(includedBinLabels);
            return `(${hexFacetId} in ${jsonIncludedBinLabels})`;
        }
    }
});

const IntervalFacetFilter = FacetFilter.extend({
    asExpression: function () {
        let filterExpressions = _.chain(this._filters)
            // Because '__null__' has no high or low bound, it must be handled specially
            .pick((binIncluded, binLabel) => {
                return binIncluded === false && binLabel !== '__null__';
            })
            // Parse range labels, to yield an array of numeric range arrays
            .map((binIncluded, binLabel) => {
                let rangeMatches = binLabel.match(/\[([\d.]+) - ([\d.]+)\)/);
                let lowBound = parseFloat(rangeMatches[1]);
                let highBound = parseFloat(rangeMatches[2]);
                return [lowBound, highBound];
            })
            .sortBy(_.identity)
            // Combine adjacent ranges
            .reduce((allRanges, curRange) => {
                let prevRange = _.last(allRanges);
                // Compare the previous high bound and the current low bound, checking for
                // the special case of the first element where there's no "prevRange"
                if (prevRange && prevRange[1] === curRange[0]) {
                    // If they match, combine the current high bound with the previous low
                    // bound
                    let combinedRange = [prevRange[0], curRange[1]];
                    // Pop the previous range, and add the combined range
                    return allRanges.slice(0, -1).concat([combinedRange]);
                } else {
                    // If there's no match, just push the current range onto the list
                    return allRanges.concat([curRange]);
                }
            }, [])
            // Convert each range into a string expression
            .map((range) => {
                let hexFacetId = SerializeFilterHelpers._stringToHex(this.facetId);
                let lowBoundExpression = `not (${hexFacetId} >= ${range[0]})`;
                let highBoundExpression = `not (${hexFacetId} < ${range[1]})`;
                return `(${lowBoundExpression} or ${highBoundExpression})`;
            })
            .value();
        if (this._filters['__null__'] === false) {
            // This conditional will also intentionally fail if '__null__' is undefined
            let hexFacetId = SerializeFilterHelpers._stringToHex(this.facetId);
            let jsonNullArray = JSON.stringify([SerializeFilterHelpers._stringToHex('__null__')]);
            filterExpressions.push(`(${hexFacetId} not in ${jsonNullArray})`);
        }
        if (_.size(filterExpressions) === 0) {
            // If none are excluded, return no filter
            return '';
        } else {
            // Combine all expressions
            return `(${filterExpressions.join(' and ')})`;
        }
    }
});

const SerializeFilterHelpers = {
    _stringToHex: function (value) {
        let result = '';
        for (let i = 0; i < value.length; i += 1) {
            result += `%${value.charCodeAt(i).toString(16)}`;
        }
        return result;
    },

    _dehexify: function (obj) {
        if (!obj) {
            return obj;
        }
        if (_.isObject(obj)) {
            if (_.isArray(obj)) {
                _.each(obj, (d, i) => {
                    obj[i] = SerializeFilterHelpers._dehexify(d);
                });
            } else {
                _.each(Object.keys(obj), (k) => {
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
            let attrType = FACET_SCHEMA[obj.identifier].coerceToType;
            if (attrType !== 'object') {
                // 'object' is really a passthrough; don't attempt
                // any coercion while performing the filter
                obj.type = attrType;
            }
        } else if (_.isArray(obj)) {
            _.each(obj, (d, i) => {
                obj[i] = SerializeFilterHelpers._specifyAttrTypes(d);
            });
        } else {
            _.each(Object.keys(obj), (k) => {
                obj[k] = SerializeFilterHelpers._specifyAttrTypes(obj[k]);
            });
        }
        return obj;
    }
};

export default ImagesFilter;
export {CategoricalFacetFilter, IntervalFacetFilter, TagsCategoricalFacetFilter};

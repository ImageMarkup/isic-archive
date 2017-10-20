import _ from 'underscore';

import { restRequest } from 'girder/rest';
import GirderCollection from 'girder/collections/Collection';

const Collection = GirderCollection.extend({
    model: null,

    url: function () {
        return this.resourceName;
    },

    fetch: function (params, reset) {
        // If "reset" is false, then reuse any unspecified params from the last
        // fetch; "reset" defaults to true (so undefined will still reset)
        if (reset === false) {
            this.params = _.extend(this.params || {}, params);
        } else {
            this.params = params || {};
        }

        // Upstream Girder contains a bug where parameters are not honored on a
        // reset fetch, so set the parameters manually before triggering a fetch
        // with (ignored) params set to null, and the reset flag set to true.
        // Doing a non-reset fetch causes the collection to not be emptied on
        // an empty fetch, and does non-intuitive things with the "this.offset"
        // property.
        // GirderCollection.prototype.fetch.call(this, null, true);

        // Re-implement GirderCollection.prototype.fetch until Girder fix #1974 is included
        this.offset = 0;
        let limit = this.pageLimit > 0 ? this.pageLimit + 1 : 0;
        let xhr = restRequest({
            url: this.altUrl || this.resourceName,
            data: _.extend({
                limit: limit,
                offset: this.offset,
                sort: this.sortField,
                sortdir: this.sortDir
            }, this.params)
        }).done((list) => {
            if (this.pageLimit > 0 && list.length > this.pageLimit) {
                // This means we have more pages to display still. Pop off
                // the extra that we fetched.
                list.pop();
                this._hasMorePages = true;
            } else {
                this._hasMorePages = false;
            }
            this.offset += list.length;
            this.reset(list);
            this.trigger('g:changed');
        });
        xhr.girder = {fetch: true};
        return xhr;
    },

    _currentOffset: function (params) {
        // "this.offset" is not reliable, especially since we're doing a reset
        // fetch in the upstream call
        if (params && params.offset) {
            // specified explicitly in the function call
            return params.offset;
        } else if (this.params && this.params.offset) {
            // taken from the previous fetch
            return this.params.offset;
        } else {
            // default, as this was never fetched, or the previous fetch was
            // unspecified (and defaulted to 0, per the upstream logic)
            return 0;
        }
    },

    hasPreviousPage: function () {
        return this._currentOffset() > 0;
    },

    // "hasNextPage" should work fine in the upstream implementation

    fetchPreviousPage: function (params) {
        let offset = this._currentOffset(params) - this.pageLimit;
        offset = Math.max(0, offset);
        this.fetch(_.extend(params || {}, {offset: offset}), false);
    },

    fetchNextPage: function (params) {
        let offset = this._currentOffset(params) + this.pageLimit;
        this.fetch(_.extend(params || {}, {offset: offset}), false);
    },

    fetchFirstPage: function (params) {
        this.fetch(_.extend(params || {}, {offset: 0}), false);
    },

    fetchLastPage: function (total, params) {
        let offset = Math.floor(total / this.pageLimit) * this.pageLimit;
        if (total % this.pageLimit === 0) {
            // there are a "pageLimit" number of elements in the last page, so
            // the math needs to be adjusted
            offset -= this.pageLimit;
            offset = Math.max(0, offset);
        }
        this.fetch(_.extend(params || {}, {offset: offset}), false);
    },

    pageNum: function () {
        return Math.floor(this._currentOffset() / this.pageLimit);
    }
});

export default Collection;

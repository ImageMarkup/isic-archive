import ImageDetailsPane from './Detail/ImageDetailsPane';
import ImagesFacetsPane from './Facets/ImagesFacetsPane';
import ImagesPagingPane from './Listing/ImagesPagingPane';
import ImageWall from './Listing/ImageWall';
import ImagesFacetCollection from './ImagesFacetCollection';
import ImagesFilter from './ImagesFilter';
import {SelectableImageCollection} from '../collections/ImageCollection';
import View from '../view';

import ImagesPageTemplate from './imagesPage.pug';
import './imagesPage.styl';

const ImagesView = View.extend({
    initialize: function (settings) {
        this.completeFacets = new ImagesFacetCollection();
        // TODO: when filteredFacets fetch returns no images, all models are gone / removed
        this.filteredFacets = new ImagesFacetCollection();
        this.filters = new ImagesFilter();

        this.images = new SelectableImageCollection();
        this.images.pageLimit = 50;

        this.listenTo(this.completeFacets, 'sync', this.onCompleteFacetsFetched);
        this.listenTo(this.filters, 'change', this.onFiltersChanged);
        this.listenTo(this.images, 'select:one', this.onImageSelected);
        // Collection resets do not trigger "deselect" events, so they must be listened for
        this.listenTo(this.images, 'deselect:one reset', this.onImageDeselected);

        this.render();
    },

    render: function () {
        this.$el.html(ImagesPageTemplate());

        // This will self-render when this.completeFacets updates
        this.facetsPane = new ImagesFacetsPane({
            completeFacets: this.completeFacets,
            filteredFacets: this.filteredFacets,
            filters: this.filters,
            el: this.$('#isic-images-facetsPane'),
            parentView: this
        });

        // This will self-render when this.images updates
        this.imageWall = new ImageWall({
            images: this.images,
            el: this.$('.isic-images-imageWall'),
            parentView: this
        });

        // This will self-render immediately
        this.pagingPane = new ImagesPagingPane({
            completeFacets: this.completeFacets,
            filteredFacets: this.filteredFacets,
            images: this.images,
            filters: this.filters,
            el: this.$('#isic-images-pagingPane'),
            parentView: this
        });

        // This kicks off the loading and rendering of all data
        this.completeFacets.fetch();

        // TODO: Issue an "images.fetch()" here too, so it can run in parallel with
        // "completeFacets.fetch()"; unfortunately, ImageWall depends on completeFacets being
        // completely loaded before "images" resolves

        return this;
    },

    onCompleteFacetsFetched: function (collection, resp, options) {
        // "ImagesFilter.initialize" doesn't trigger any events, so run it first, to ensure
        // this.filters is populated before "this.filteredFacets" is populated (as that does have
        // multiple event handlers attached to it)
        this.filters.initialize(collection);

        // Rather than issue a second fetch request for this.filteredFacets,
        // copy the response of the first request for this.completeFacets
        // TODO: ideally, this.filteredFacets would only be reset when
        // this.completeFacets triggered an "update" (which would prevent resets when
        // "sync" had no changes); however, it's difficult to deep-copy all of
        // the models from this.completeFacets to this.filteredFacets without having
        // access to the raw HTTP response
        this.filteredFacets.reset(resp, {parse: true});

        this.images.fetch();
    },

    onFiltersChanged: function () {
        // Cancel any previous still-pending requests, as this new set of requests will override
        // them anyway
        if (this.filteredFacets._pendingRequest) {
            this.filteredFacets._pendingRequest.abort();
        }
        if (this.images._pendingRequest) {
            this.images._pendingRequest.abort();
        }

        // TODO: If there's no "filterQuery", we could just always reset "filteredFacets" to
        // "completeFacets" here; then make "filters.initialize" trigger a "change" event
        // when called; then remove the calls to "images.fetch" and "filteredFacets.reset"
        // from the "onCompleteFacetsFetched" handler and let them just run from here only

        let filterQuery = JSON.stringify(this.filters.asAst());
        this.filteredFacets._pendingRequest = this.filteredFacets.fetch({
            // filteredFacets is a direct subclass of Backbone.Collection, with different
            // arguments to ".fetch"
            data: {
                filter: filterQuery
            }
        });
        this.images._pendingRequest = this.images.fetch({
            offset: 0,
            filter: filterQuery
        });

        // TODO: It would be nice if collections just automatically stored their most recent
        // fetch XHR as an internal property.
    },

    _clearDetailsPane: function () {
        if (this.imageDetailsPane) {
            // Girder's version of "destroy" (unlike Backbone's "remove") will empty, but not
            // remove "imageDetailsPane.$el"
            this.imageDetailsPane.destroy();
            this.imageDetailsPane = null;
        }
    },

    onImageSelected: function () {
        this._clearDetailsPane();
        // This will self-render when the image details are available
        this.imageDetailsPane = new ImageDetailsPane({
            image: this.images.selected,
            el: this.$('#isic-images-imageDetailsPane'),
            parentView: this
        });
    },

    onImageDeselected: function () {
        if (!this.images.selected) {
            this._clearDetailsPane();
        }
        // If another image is selected, do nothing, as the "select:one" event (which unfortunately
        // gets triggered before "deselect:one") should have already run
    }
});

export default ImagesView;

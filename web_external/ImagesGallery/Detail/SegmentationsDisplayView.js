import $ from 'jquery';

import {getApiRoot} from 'girder/rest';

import {SelectableSegmentationCollection} from '../../collections/SegmentationCollection';
import View from '../../view';

import SegmentationDisplayPageTemplate from './segmentationDisplayPage.pug';
import './segmentationDisplayPage.styl';
import SegmentationsDisplayPageTemplate from './segmentationsDisplayPage.pug';
import './segmentationsDisplayPage.styl';

/**
 * View for displaying an image segmentation's properties
 */
const SegmentationDisplayView = View.extend({
    /**
     * @param {SegmentationModel} settings.model
     */
    initialize: function (settings) {
        if (this.model.has('meta')) {
            this.render();
        } else {
            // Since this view doesn't own the "model", "listenTo" absolutely must be used
            this.listenTo(this.model, 'g:fetched', this.render);
            this.model.fetch();
        }
    },

    render: function () {
        let created = this.formatDate(this.model.get('created'));
        let thumbnailUrl = [
            getApiRoot(),
            'segmentation',
            this.model.id,
            'thumbnail?width=256'
        ].join('/');

        this.$el.html(SegmentationDisplayPageTemplate({
            segmentation: this.model,
            created: created,
            thumbnailUrl: thumbnailUrl,
            stringify: this._stringify
        }));

        return this;
    },

    _stringify: function (val) {
        return JSON.stringify(val, null, 4);
    }
});

/**
 * View for selecting an image segmentation and displaying its properties
 */
const SegmentationsDisplayView = View.extend({
    events: {
        'change select': function (event) {
            let selectedSegmentationId = $(event.currentTarget).val();
            let selectedSegmentation = this.segmentations.get(selectedSegmentationId);
            selectedSegmentation.select();
        }
    },

    /**
     * @param {ImageModel} settings.image
     */
    initialize: function (settings) {
        this.image = settings.image;

        this.segmentations = new SelectableSegmentationCollection();
        this.segmentations.pageLimit = Number.MAX_SAFE_INTEGER;
        this.listenTo(this.segmentations, 'g:changed', this.render);
        this.listenTo(this.segmentations, 'select:one', this.onSelected);

        this.segmentationDisplayView = null;

        this.segmentations.fetch({
            imageId: this.image.id
        });
    },

    render: function () {
        this.$el.html(SegmentationsDisplayPageTemplate({
            segmentations: this.segmentations
        }));

        return this;
    },

    onSelected: function (selectedSegmentation) {
        if (this.segmentationDisplayView) {
            this.segmentationDisplayView.destroy();
            this.segmentationDisplayView = null;
        }
        this.segmentationDisplayView = new SegmentationDisplayView({
            model: selectedSegmentation,
            el: this.$('#isic-segmentation-display-container'),
            parentView: this
        });
    }
});

export default SegmentationsDisplayView;

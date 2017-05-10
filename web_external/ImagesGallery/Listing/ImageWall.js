import $ from 'jquery';

import ImageFullscreenWidget from '../../common/Viewer/ImageFullscreenWidget';
import View from '../../view';

import ImageWallTemplate from './imageWall.pug';

var ImageWall = View.extend({
    events: {
        'click .thumb': function (event) {
            var imageId = $(event.currentTarget).data('imageId');
            var clickedImage = this.images.get(imageId);

            if (event.shiftKey) {
                new ImageFullscreenWidget({ // eslint-disable-line no-new
                    el: $('#g-dialog-container'),
                    model: clickedImage,
                    parentView: this
                }).render();
            } else {
                clickedImage.toggleSelected();
            }
        }
    },

    /**
     * @param {SelectableImageCollection} settings.images
     */
    initialize: function (settings) {
        this.images = settings.images;
        // For now we'll hard code this (and probably change it in the future), depending on the
        // page size
        this.thumbnailSize = 128;

        // TODO: could this event be simply 'update'? (it should not fire when sub-models are directly fetched)
        this.listenTo(this.images, 'g:changed', this.render);
        this.listenTo(this.images, 'select:one deselect:one', this._rerenderSelection);
    },

    render: function () {
        // Since tooltip-enabled elements are about to be destroyed, first remove any active
        // tooltips from them.
        this.clearTooltips();

        this.$el.html(ImageWallTemplate({
            apiRoot: this.apiRoot,
            images: this.images.models,
            thumbnailSize: this.thumbnailSize
        }));

        this.$('[data-toggle="tooltip"]').tooltip({
            placement: 'auto',
            viewport: '#isic-images-imageWall',
            trigger: 'hover'
        });
    },

    _rerenderSelection: function () {
        this.$('.thumb').removeClass('selected');

        var selectedImage = this.images.selected;
        if (selectedImage) {
            this.$('.thumb[data-image-id="' + selectedImage.id + '"]').addClass('selected');
        }
    },

    clearTooltips: function () {
        this.$('[data-toggle="tooltip"]').tooltip('hide');
        // For unknown reasons, tooltips sometimes remain after they've been hidden, so manually
        // destroy the tooltip element.
        this.$('.tooltip').remove();
    }
});

export default ImageWall;

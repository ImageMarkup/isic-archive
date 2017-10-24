import $ from 'jquery';
import 'bootstrap/js/tooltip';

import {getApiRoot} from 'girder/rest';

import ImageFullscreenWidget from '../../common/Viewer/ImageFullscreenWidget';
import View from '../../view';

import ImageWallTemplate from './imageWall.pug';
import './imageWall.styl';

const ImageWall = View.extend({
    className: 'isic-images-imageWall',

    events: {
        'click .isic-images-imageWall-thumbnail': function (event) {
            let imageId = $(event.currentTarget).data('imageId');
            let clickedImage = this.images.get(imageId);

            if (event.shiftKey) {
                this._showImageZoomModal(clickedImage);
            } else {
                clickedImage.toggleSelected();
            }
        },

        'click .isic-images-imageWall-zoom': function (event) {
            event.stopPropagation();

            let imageId = $(event.currentTarget).parent().parent().data('imageId');
            let clickedImage = this.images.get(imageId);

            this._showImageZoomModal(clickedImage);
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
        this.$el.html(ImageWallTemplate({
            apiRoot: getApiRoot(),
            images: this.images,
            thumbnailHeight: this.thumbnailSize * 0.75,
            thumbnailWidth: this.thumbnailSize
        }));

        this.$('[title]').tooltip({
            placement: 'auto',
            viewport: this.$el,
            trigger: 'hover'
        });

        return this;
    },

    _rerenderSelection: function () {
        this.$('.isic-images-imageWall-thumbnail').removeClass('selected');

        let selectedImage = this.images.selected;
        if (selectedImage) {
            this.$(`.isic-images-imageWall-thumbnail[data-image-id="${selectedImage.id}"]`).addClass('selected');
        }
    },

    _showImageZoomModal: function (image) {
        new ImageFullscreenWidget({ // eslint-disable-line no-new
            el: $('#g-dialog-container'),
            model: image,
            parentView: this
        }).render();
    }
});

export default ImageWall;

import _ from 'underscore';

import ImageViewerWidget from './ImageViewerWidget';
import View from '../../view';

import ImageFullscreenWidgetTemplate from './imageFullscreenWidget.pug';
import './imageFullscreenWidget.styl';

var ImageFullscreenWidget = View.extend({
    render: function () {
        this.$el.html(ImageFullscreenWidgetTemplate({
            model: this.model
        })).girderModal(this).on('shown.bs.modal', _.bind(function () {
            this.imageViewerWidget = new ImageViewerWidget({
                el: this.$('.isic-image-fullscreen-container'),
                model: this.model,
                parentView: this
            }).render();
        }, this)).on('hidden.bs.modal', _.bind(function () {
            if (this.imageViewerWidget) {
                this.imageViewerWidget.destroy();
                delete this.imageViewerWidget;
            }
        }, this));
    }
});

export default ImageFullscreenWidget;

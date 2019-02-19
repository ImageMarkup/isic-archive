import ImageViewerWidget from './ImageViewerWidget';
import View from '../../view';

import ImageFullscreenWidgetTemplate from './imageFullscreenWidget.pug';
import './imageFullscreenWidget.styl';

const ImageFullscreenWidget = View.extend({
    render: function () {
        this.$el.html(ImageFullscreenWidgetTemplate({
            model: this.model
        }))
            .girderModal(this)
            .on('shown.bs.modal', () => {
                this.imageViewerWidget = new ImageViewerWidget({
                    el: this.$('.isic-image-fullscreen-container'),
                    model: this.model,
                    parentView: this
                }).render();
            })
            .on('hidden.bs.modal', () => {
                if (this.imageViewerWidget) {
                    this.imageViewerWidget.destroy();
                    delete this.imageViewerWidget;
                }
            });

        return this;
    }
});

export default ImageFullscreenWidget;

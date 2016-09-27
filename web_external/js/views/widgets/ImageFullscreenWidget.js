isic.views.ImageFullscreenWidget = isic.View.extend({
    events: {
        'click': function (event) {
            this.$el.modal('hide');
        }
    },

    initialize: function (settings) {
        this.render();
    },

    render: function () {
        this.$el.html(isic.templates.imageFullscreenWidget());

        var img = this.$('.focusimage');

        // Supply the image element with a new src attribute to display the image.
        var src = '/api/v1/image/' + this.model.id + '/download?contentDisposition=inline';
        img.attr('src', src);

        // Create a dummy image element so we can learn the size of the new image.
        // When the image is loaded, we can use its size to properly resize and
        // situate the modal.
        var image = new Image();
        image.onload = _.bind(function () {
            // Add thirty to represent the 15px padding that comes stock with a
            // Bootstrap modal.
            var modalWidth = image.width + 30;
            var modalHeight = image.height + 30;

            // Set the CSS of the dialog so it appears vertically and horizontally
            // centered in the webpage (even with browser resizing).
            this.$el.find('.modal-dialog').css({
                width: modalWidth + 'px',
                position: 'absolute',
                top: '50%',
                left: '50%',
                'margin-top': (-modalHeight / 2) + 'px',
                'margin-left': (-modalWidth / 2) + 'px'
            });

            // Now that the image and CSS are ready, show the modal.
            this.$el.modal('show');
        }, this);

        image.src = src;
    }
});

isic.views.ImagesViewSubViews = isic.views.ImagesViewSubViews || {};

// View for image details
isic.views.ImagesViewSubViews.ImageDetailsPane = isic.View.extend({
    events: {
        'click .button': 'clearSelectedImage',
        'click .openwindow': 'openwindow',
        'click .fullscreen': 'fullscreen'
    },

    initialize: function (settings) {
        this.image = settings.image;

        this.listenTo(this.image, 'changed:_id g:fetched g:error', this.render);

        this.segmentationsDisplayView = new isic.views.SegmentationsDisplayView({
            image: this.image,
            parentView: this
        });

    },

    render: function () {
        var created = null;
        var license = {
            name: null,
            url: null
        };
        var acquisitionMetadata = null;
        var clinicalMetadata = null;

        // Get image data
        if (this.image.id) {
            created = girder.formatDate(this.image.get('created'), girder.DATE_SECOND);

            // Get license, default to CC-0
            if (this.image.has('license')) {
                license.name = this.image.get('license');
            } else {
                license.name = 'CC-0';
                license.url = 'https://creativecommons.org/publicdomain/zero/1.0/';
            }

            var meta = this.image.get('meta');
            acquisitionMetadata = meta['acquisition'];
            clinicalMetadata = meta['clinical'];

            // Reformat some acquisition metadata
            acquisitionMetadata['Dimensions (pixels)'] =
                acquisitionMetadata['pixelsX'] + ' &times; ' + acquisitionMetadata['pixelsY'];
            delete acquisitionMetadata['pixelsX'];
            delete acquisitionMetadata['pixelsY'];
        }

        this.$el.html(isic.templates.imageDetailsPage({
            imgRoot: girder.staticRoot + '/built/plugins/isic_archive/extra/img',
            image: this.image,
            created: created,
            license: license,
            acquisitionMetadata: acquisitionMetadata,
            clinicalMetadata: clinicalMetadata
        }));

        this.segmentationsDisplayView.setElement(
            this.$('#isic-image-details-segmentations-display-view-container')).render();

        this.initializeTooltips();

        return this;
    },

    openwindow: function () {
      this.clearTooltips();
      window.open('/api/v1/image/' + this.image.id + '/download?contentDisposition=inline');
    },

    fullscreen: function () {
      this.clearTooltips();

      var img = $('.focusimage');
      var modal = $('#focusmodal');

      // Supply the image element with a new src attribute to display the image.
      var src = '/api/v1/image/' + this.image.id + '/download?contentDisposition=inline';
      img.attr('src', src);

      // Create a dummy image element so we can learn the size of the new image.
      // When the image is loaded, we can use its size to properly resize and
      // situate the modal.
      var image = new Image();
      image.onload = function () {
        // Add thirty to represent the 15px padding that comes stock with a
        // Bootstrap modal.
        var modalWidth = image.width + 30;
        var modalHeight = image.height + 30;

        // Set the CSS of the dialog so it appears vertically and horizontally
        // centered in the webpage (even with browser resizing).
        modal.find('.modal-dialog').css({
          width: modalWidth + 'px',
          position: 'absolute',
          top: '50%',
          left: '50%',
          'margin-top': (-modalHeight / 2) + 'px',
          'margin-left': (-modalWidth / 2) + 'px'
        });

        // Now that the image and CSS are ready, show the modal.
        modal.modal('show');
      };

      // Allow clicking on the image itself to dismiss the modal.
      img.on('click.dismiss', function () {
        $('#focusmodal').modal('hide');
      });

      image.src = src;
    },

    clearSelectedImage: function () {
        this.image.clear();
    },

    initializeTooltips: function () {
        this.$('[data-toggle="tooltip"]').tooltip({
            trigger: 'hover'
        });
    },

    clearTooltips: function () {
      $('[data-toggle="tooltip"]').tooltip('hide');
    }
});

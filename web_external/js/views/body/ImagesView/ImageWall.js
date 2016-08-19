/*globals girder, jQuery, d3, Image, Backbone, _*/
/*eslint-disable*/
var LOG_IMAGE_FETCHES = false;

var INITIAL_IMAGES_TO_FETCH = 150;

// We scaled the images based on how many
// are currently selected; for now we'll hard
// code this (and probably change it in the future)
var temp_download_size = 10000;

isic.views.ImagesSubViews = isic.views.ImagesSubViews || {};

isic.views.ImagesSubViews.ImageWall = Backbone.View.extend({
  initialize: function () {
    var self = this;
    self.imageCache = {};
    self.loadedImages = {};
    self.imageColumnLookup = {};
    self.imageColumns = [];

    self.imageIds = [];

    // Re-render when the window
    // changes size
    window.onresize = function () {
      self.render();
    };
  },
  setImages: function (imageIds) {
    var self = this;

    self.imageIds = imageIds;
    self.loadedImages = {};

    // Start fetching the images now... don't wait
    // around for the call in render()
    self.imageIds.forEach(function (i) {
      if (!self.imageCache.hasOwnProperty(i)) {
        self.imageCache[i] = new Image();
        self.imageCache[i].addEventListener('load', function () {
          if (!self.imageCache[i].width || !self.imageCache[i].height) {
            self.handleBadImage(i);
          } else {
            self.loadedImages[i] = true;
          }
          self.render();
        });
        self.imageCache[i].addEventListener('error', function () {
          self.handleBadImage(i);
        });
        self.imageCache[i].src = girder.apiRoot + '/image/' + i +
            '/thumbnail';
      }
    });

    // Clear out any old IDs after a while
    // (don't do it immediately in case the
    // user is flipping back and forth between
    // pages)
    window.setTimeout(function () {
      Object.keys(self.imageCache).forEach(function (i) {
        if (self.imageIds.indexOf(i) === -1) {
          delete self.imageCache[i];
          delete self.loadedImages[i];
        }
      });
    }, 100000);

    self.render();
  },
  handleBadImage: function (imageId) {
    var self = this;
    // The image didn't load correctly; replace it with the "no thumbnail
    // available" image
    self.imageCache[imageId].src = girder.staticRoot +
      '/built/plugins/isic_archive/extra/img/noThumbnail.svg';
  },
  rearrangeColumns: function (numColumns) {
    var self = this;
    var imageId, myColumn, myIndex;
    /*
    Here we lay out which images go where; we want an image
    to stay in the same column, in the same order, as long
    as that image is on the page, with the exception of
    balancing
    */

    // Remove any images that aren't here any more
    Object.keys(self.imageColumnLookup).forEach(function (imageId) {
      if (self.imageIds.indexOf(imageId) === -1) {
        myColumn = self.imageColumnLookup[imageId];
        myIndex = self.imageColumns[myColumn].indexOf(imageId);

        self.imageColumns[myColumn].splice(myIndex, 1);
        delete self.imageColumnLookup[imageId];
      }
    });

    // Figure out which new images need placing
    var imagesToPlace = [];

    Object.keys(self.loadedImages).forEach(function (imageId) {
      if (!self.imageColumnLookup.hasOwnProperty(imageId)) {
        // For some reason, browsers seem to be
        // loading the images backwards. For a
        // better top-down effect (especially
        // when images are fetched in bulk), I'm
        // inserting them at the beginning
        imagesToPlace.splice(0, 0, imageId);
      }
    });

    // Add or remove columns as necessary (images in
    // a dying column need to be placed again)
    while (self.imageColumns.length < numColumns) {
      self.imageColumns.push([]);
    }
    while (self.imageColumns.length > numColumns) {
      var dyingColumn = self.imageColumns.pop();
      if (dyingColumn) {
        dyingColumn.forEach(function (imageId) {
          delete self.imageColumnLookup[imageId];
          imagesToPlace.push(imageId);
        });
      }
    }

    // Helper function for placing/balancing
    // columns of images:
    function minAndMaxIndices() {
      var result = {
        minIndices: [],
        maxIndices: [],
        min: undefined,
        max: undefined,
        minLength: Infinity,
        maxLength: 0
      };

      self.imageColumns.forEach(function (column, index) {
        if (column.length > result.maxLength) {
          result.maxLength = column.length;
          result.maxIndices = [index];
        } else if (column.length === result.maxLength) {
          result.maxIndices.push(index);
        }
        if (column.length < result.minLength) {
          result.minLength = column.length;
          result.minIndices = [index];
        } else if (column.length === result.minLength) {
          result.minIndices.push(index);
        }
      });

      // Choose the single min and max columns randomly
      result.min = Math.floor(Math.random() * result.minIndices.length);
      result.min = result.minIndices[result.min];
      result.max = Math.floor(Math.random() * result.maxIndices.length);
      result.max = result.maxIndices[result.max];

      return result;
    }

    // Consume imagesToPlace by putting images
    // in one of the least-full columns
    while (imagesToPlace.length > 0) {
      imageId = imagesToPlace.pop();
      myColumn = minAndMaxIndices().min;

      self.imageColumns[myColumn].push(imageId);
      self.imageColumnLookup[imageId] = myColumn;
    }

    // Balance the columns
    var minAndMax = minAndMaxIndices();
    while (minAndMax.maxLength - minAndMax.minLength > 3) {
      // Allow a ragged bottom edge... the gap can be as much as 3
      imageId = self.imageColumns[minAndMax.max].pop();
      self.imageColumns[minAndMax.min].push(imageId);
      self.imageColumnLookup[imageId] = minAndMax.min;
      minAndMax = minAndMaxIndices();
    }
  },
  render: _.debounce(function () {
    var self = this;

    if (!this.addedSvgElement) {
      d3.select(this.el).append('svg')
        .attr('id', 'preview');
    }

    // Temporarily force scroll bars so that we can account for their width
    this.$el.css('overflow', 'scroll');
    var width = this.el.clientWidth;
    this.$el.css('overflow', '');

    // We want the width of each column of images to have an
    // inverse relationship with the size of the download, so
    // more, smaller thumbnails show up when the download is large)
    var columnScale = d3.scale.linear()
      .domain([0, temp_download_size])
      .range([256, 256 / 4]); // Shrink the thumbnails by as much as a quarter

    var imageWidth = columnScale(temp_download_size);

    var imagePadding = 5;

    // We'll do a little sneaky scaling up so the images
    // are flush with the edge
    var numColumns = Math.floor((width - imagePadding) /
      (imageWidth + imagePadding));
    numColumns = Math.max(numColumns, 1);
    imageWidth = (width - imagePadding) / numColumns - imagePadding;

    // Okay, we know how many columns we can fit...
    // figure out where all the images go:
    self.rearrangeColumns(numColumns);

    // Okay, time to draw / move the pictures:
    var images = d3.select('#preview').selectAll('image')
      .data(self.imageIds, function (d) {
        return d;
      });
    images.enter().append('image')
      .attr({
        'id': function (d) {
          return 'image' + d;
        },
        'xlink:href': function (d) {
          return self.imageCache[d].src;
        },
        'preserveAspectRatio': 'xMinYMin',
        'x': width / 2, // Start new images at the middle of the
        'y': jQuery('#preview').height() // bottom of the screen
      })
      .on('click', function (d) {
        // TODO: show a lightbox
        // For now, jump to the item in girder
        window.open('#item/' + d);
      });

    // Construct a position/height lookup dict
    // (we want to animate everything at the same
    // time, so don't actually set these values
    // until we know them)
    var placementLookup = {};
    var tallestHeight = 0;
    var missingImages = 0;
    var availableImages = 0;
    self.imageColumns.forEach(function (column, index) {
      var y = imagePadding;
      column.forEach(function (imageId) {
        // Calculate the natural height of the image
        var height;
        availableImages += 1;
        height = self.imageCache[imageId].height * imageWidth /
          self.imageCache[imageId].width;
        placementLookup[imageId] = {
          x: imagePadding + index * (imageWidth + imagePadding),
          y: y,
          height: height
        };
        y += height + imagePadding;

        if (y > tallestHeight) {
          tallestHeight = y;
        }
      });
    });

    // After all that, we finally know how much space we need
    d3.select('#preview').attr({
      'width': width,
      'height': tallestHeight
    });

    // Animation time! Move / resize stuff:
    images.filter(function (d) {
      return placementLookup.hasOwnProperty(d);
    }).transition().duration(500)
      .attr({
        width: imageWidth,
        height: function (d) {
          return placementLookup[d].height;
        },
        x: function (d) {
          return placementLookup[d].x;
        },
        y: function (d) {
          return placementLookup[d].y;
        }
      });
  }, 300)
});

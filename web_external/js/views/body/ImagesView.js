/*globals girder, jQuery, d3, Image*/
/*eslint-disable*/
var LOG_IMAGE_FETCHES = false;

var INITIAL_IMAGES_TO_FETCH = 150;

function widthWithoutScrollbar(selector) {
  var tempDiv = jQuery('<div/>');
  jQuery(selector).append(tempDiv);
  var elemwidth = tempDiv.width();
  tempDiv.remove();
  return elemwidth;
}

// We scaled the images based on how many
// are currently selected; for now we'll hard
// code this (and probably change it in the future)
var temp_download_size = 10000;

isic.views.ImagesView = isic.View.extend({
  initialize: function () {
    var self = this;
    self.imageCache = {};
    self.imageColumnLookup = {};
    self.imageColumns = [];

    self.currentImageOffset = 0;
    self.imageIds = [];

    self.$el.html(isic.templates.imagesPage());
    self.fetchImageTimeout = null;
    self.fetchImages();

    // Re-render when the window
    // changes size
    window.onresize = function () {
      self.render();
    };
    // Load more images when we hit the bottom
    // of the content area
    jQuery('#isic-images-pageContent').on('scroll', function () {
      // If we haven't sent an initial request,
      // do it immediately (don't wait for the
      // scroll to finish to start fetching images)
      if (self.fetchImageTimeout === null) {
        // self.fetchImages();
      } else {
        // Otherwise debounce the scrolling
        window.clearTimeout(self.fetchImageTimeout);
      }

      self.fetchImageTimeout = window.setTimeout(function () {
        self.fetchImageTimeout = null;
        self.fetchImages();
      }, 300);
    });
  },
  fetchImages: function (numberToFetch) {
    var self = this;

    if (!numberToFetch) {
      if (self.averageImageSize === undefined) {
        numberToFetch = INITIAL_IMAGES_TO_FETCH;
      } else {
        // Estimate how many more images we need
        var bounds = jQuery('#isic-images-preview')[0].getBoundingClientRect();
        var content = jQuery('#isic-images-pageContent');
        var spaceLeft = content.scrollTop() + content.height() - bounds.bottom;
        numberToFetch = Math.floor(self.imageColumns.length *
          (spaceLeft / self.averageImageSize));

        if (numberToFetch <= 0) {
          // If a negligible amount of space is left,
          // don't bother getting any more until
          // the user scrolls again
          return;
        }
      }
    }

    girder.restRequest({
      path: 'image',
      data: {
        'limit': numberToFetch,
        'offset': self.currentImageOffset
      }
    }).done(function (newImageList) {
      var newImageIds = newImageList.map(function(obj) {
        return obj._id;
      });
      self.imageIds = self.imageIds.concat(newImageIds);

      // Start fetching the images now... don't wait
      // around for the call in render()
      newImageIds.forEach(function (i) {
        if (!self.imageCache.hasOwnProperty(i)) {
          self.imageCache[i] = new Image();
          self.imageCache[i].src = girder.apiRoot + '/image/' + i +
              '/thumbnail';
        }
      });

      self.currentImageOffset += newImageIds.length;

      if (LOG_IMAGE_FETCHES) {
        console.log(newImageIds.length + ' images received for a total of ' +
          self.currentImageOffset);
      }

      self.render();

      // Go get more if we need them
      self.fetchImages();
    });
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
    // TODO(maybe): this is suboptimal in a bunch of ways...
    for (imageId in self.imageColumnLookup) {
      if (self.imageIds.indexOf(imageId) === -1) {
        myColumn = self.imageColumnLookup[imageId];
        myIndex = self.imageColumns[myColumn].indexOf(imageId);

        self.imageColumns[myColumn].splice(myIndex, 1);

        delete self.imageColumnLookup[imageId];
        delete self.imageCache[imageId];
      }
    }

    // Figure out which new images need placing
    var imagesToPlace = [];

    self.imageIds.forEach(function (imageId) {
      if (!self.imageColumnLookup.hasOwnProperty(imageId)) {
        // For some reason, browser seem to be
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
      dyingColumn.forEach(function (imageId) {
        delete self.imageColumnLookup[imageId];
        imagesToPlace.push(imageId);
      });
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
  renderImages: function () {
    var self = this;

    // Figure out how much space we have to play with
    var width = widthWithoutScrollbar('#isic-images-pageContent');

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
    imageWidth = (width - imagePadding) / numColumns - imagePadding;

    // Okay, we know how many columns we can fit...
    // figure out where all the images go:
    self.rearrangeColumns(numColumns);

    // Okay, time to draw / move the pictures:
    var images = d3.select('#isic-images-preview').selectAll('image')
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
        'y': jQuery('#isic-images-preview').height() // bottom of the screen
      })
      .on('click', function (d) {
        // TODO: show a lightbox
        // For now, jump to the item in girder
        window.open('girder#item/' + d);
      });

    // Construct a position/height lookup dict
    // (we want to animate everything at the same
    // time, so don't actually set these values
    // until we know them)
    var placementLookup = {};
    var tallestHeight = 0;
    self.averageImageSize = 0;
    var missingImages = 0;
    var availableImages = 0;
    self.imageColumns.forEach(function (column, index) {
      var y = imagePadding;
      column.forEach(function (imageId) {
        // Calculate the natural height of the image
        var height;
        if (!self.imageCache[imageId].width ||
          !self.imageCache[imageId].height) {
          missingImages += 1;

          // The image hasn't loaded yet, so just assume
          // it's the same as the width for now (will get
          // fixed on the next render call)
          height = imageWidth;

          // While we're here, trigger an image reload
          // in case there was a server error the first time
          var url = girder.apiRoot + '/image/' + imageId + '/thumbnail';
          self.imageCache[imageId] = new Image();
          self.imageCache[imageId].src = url;
          d3.select('#image' + imageId).attr('xlink:href', url);

          // Wait a second, and try another render call to
          // fix any artifacts
          if (self.renderTimeout !== undefined) {
            window.clearTimeout(self.renderTimeout);
          }
          self.renderTimeout = window.setTimeout(function () {
            self.render();
          }, 1000);
        } else {
          availableImages += 1;

          height = self.imageCache[imageId].height * imageWidth /
            self.imageCache[imageId].width;
        }
        placementLookup[imageId] = {
          x: imagePadding + index * (imageWidth + imagePadding),
          y: y,
          height: height
        };
        y += height + imagePadding;

        self.averageImageSize += height;
        if (y > tallestHeight) {
          tallestHeight = y;
        }
      });
    });
    if (self.imageIds.length > 0) {
      self.averageImageSize = self.averageImageSize / self.imageIds.length;
    } else {
      self.averageImageSize = undefined;
    }
    if (LOG_IMAGE_FETCHES) {
      console.log(availableImages + '/' + (missingImages + availableImages) +
        ' successfully rendered.');
    }

    // After all that, we finally know how much space we need
    d3.select('#isic-images-preview').attr({
      'width': width,
      'height': tallestHeight
    });

    // Animation time! Move / resize stuff:
    images.transition().duration(500)
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
  },
  render: function () {
    var self = this;
    self.renderImages();
  }
});

isic.router.route('images', 'images', function (id) {
    girder.events.trigger('g:navigateTo', isic.views.ImagesView);
});

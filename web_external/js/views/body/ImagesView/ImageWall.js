/*globals girder, jQuery, d3, Image, Backbone, _*/

// For now we'll hard code this (and probably change it in the future),
// depending on the page size
var imageSize = 128;

isic.views.ImagesViewSubViews = isic.views.ImagesViewSubViews || {};

isic.views.ImagesViewSubViews.ImageWall = Backbone.View.extend({
    initialize: function () {
        var self = this;
        self.imageCache = {};
        self.loadedImages = {};
        self.imageColumnLookup = {};
        self.imageColumns = [];

        self.listenTo(self.model, 'change:selectedImageId', self.render);
        self.listenTo(self.model, 'change:imageIds', self.setImages);
    },
    setImages: function () {
        var self = this;
        self.loadedImages = {};

        // Start fetching the images now... don't wait
        // around for the call in render()
        self.model.get('imageIds').forEach(function (i) {
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
                    '/thumbnail?width=' + imageSize;
            } else {
                // If we already have the image cached, we can call render right
                // away (it gets debounced, so we // don't have to worry about
                // tons of render calls)
                self.loadedImages[i] = true;
                self.render();
            }
        });

        // Clear out any old IDs after a while (don't do it immediately in case
        // the user is flipping back and forth between pages)
        window.clearTimeout(self.cleanupTimeout);
        self.cleanupTimeout = window.setTimeout(function () {
            Object.keys(self.imageCache).forEach(function (i) {
                if (self.model.get('imageIds').indexOf(i) === -1) {
                    delete self.imageCache[i];
                    delete self.loadedImages[i];
                }
            });
        }, 10000);
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
            if (self.model.get('imageIds').indexOf(imageId) === -1) {
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
    selectImage: function (imageId) {
        var self = this;
        self.model.set('selectedImageId', imageId);
    },
    render: _.debounce(function () {
        var self = this;
        var svg;

        if (!this.addedSvgElement) {
            svg = d3.select(this.el).append('svg')
                .attr('id', 'preview');
            svg.append('g')
                .attr('id', 'previewContents');
            svg.append('rect')
                .attr('id', 'highlightOutline');
            this.addedSvgElement = true;
        } else {
            svg = d3.select(this.el).select('svg');
        }

        // Temporarily hide the SVG element and force scroll bars
        // so that we can figure out the actual amount of space that
        // the flex box is giving us
        this.$el.css('overflow', 'scroll');
        svg.attr({
            'width': 0
        });
        var width = this.el.clientWidth;
        this.$el.css('overflow', '');

        var imageWidth = imageSize; // TODO: something fancier...?

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

        // Construct a position/height lookup dict
        var placementLookup = {};
        var tallestHeight = 0;
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
            });
            if (y > tallestHeight) {
                tallestHeight = y;
            }
        });

        // After all that, we finally know how much space we need
        svg.attr({
            'width': width,
            'height': tallestHeight
        });

        // Okay, time to draw the pictures (in their initial positions)
        var imageList = Object.keys(self.loadedImages)
            .filter(function (d) {
                return placementLookup.hasOwnProperty(d);
            });
        var images = svg.select('#previewContents').selectAll('image')
            .data(imageList, function (d) {
                return d;
            });
        images.enter().append('image')
            .attr('preserveAspectRatio', 'xMinYMin');
        images.exit().remove();
        images.attr('id', function (d) {
            return 'image' + d;
        }).attr('xlink:href', function (d) {
            return self.imageCache[d].src;
        }).attr('class', function (d) {
            if (d === self.model.get('selectedImageId')) {
                return 'selected';
            } else {
                return null;
            }
        }).attr({
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
        }).on('click', function (d) {
            self.selectImage(d === self.model.get('selectedImageId') ? null : d);
        });

        // Draw the highlight rect
        var selectedImageId = self.model.get('selectedImageId');
        if (selectedImageId) {
            svg.select('#highlightOutline')
                .style('display', null)
                .attr({
                    x: placementLookup[selectedImageId].x,
                    y: placementLookup[selectedImageId].y,
                    width: imageWidth,
                    height: placementLookup[selectedImageId].height
                });
        } else {
            svg.select('#highlightOutline')
                .style('display', 'none');
        }
        return this;
    }, 50)
});

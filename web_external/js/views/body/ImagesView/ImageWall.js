/*globals d3*/

// For now we'll hard code this (and probably change it in the future),
// depending on the page size
var imageSize = 128;

isic.views.ImagesViewSubViews = isic.views.ImagesViewSubViews || {};

isic.views.ImagesViewSubViews.ImageWall = Backbone.View.extend({
    initialize: function (settings) {
        this.image = settings.image;
        this.imageCache = {};
        this.loadedImages = {};
        this.imageColumnLookup = {};
        this.imageColumns = [];

        this.listenTo(this.image, 'change:_id', this.render);
        this.listenTo(this.model, 'change:imageIds', this.setImages);
    },
    setImages: function () {
        this.loadedImages = {};

        // Start fetching the images now... don't wait
        // around for the call in render()
        _.each(this.model.get('imageIds'), function (i) {
            if (!_.has(this.imageCache, i)) {
                this.imageCache[i] = new Image();
                this.imageCache[i].addEventListener('load', _.bind(function () {
                    if (!this.imageCache[i].width || !this.imageCache[i].height) {
                        this.handleBadImage(i);
                    } else {
                        this.loadedImages[i] = true;
                    }
                    this.render();
                }, this));
                this.imageCache[i].addEventListener('error', _.bind(function () {
                    this.handleBadImage(i);
                }, this));
                this.imageCache[i].src = girder.apiRoot + '/image/' + i +
                    '/thumbnail?width=' + imageSize;
            } else {
                // If we already have the image cached, we can call render right
                // away (it gets debounced, so we // don't have to worry about
                // tons of render calls)
                this.loadedImages[i] = true;
                this.render();
            }
        }, this);

        // Clear out any old IDs after a while (don't do it immediately in case
        // the user is flipping back and forth between pages)
        window.clearTimeout(this.cleanupTimeout);
        this.cleanupTimeout = window.setTimeout(_.bind(function () {
            _.each(Object.keys(this.imageCache), function (i) {
                if (this.model.get('imageIds').indexOf(i) === -1) {
                    delete this.imageCache[i];
                    delete this.loadedImages[i];
                }
            }, this);
        }, this), 10000);
    },
    handleBadImage: function (imageId) {
        // The image didn't load correctly; replace it with the "no thumbnail
        // available" image
        this.imageCache[imageId].src = girder.staticRoot +
            '/built/plugins/isic_archive/extra/img/noThumbnail.svg';
    },
    rearrangeColumns: function (numColumns) {
        var imageId, myColumn, myIndex;
        /*
         Here we lay out which images go where; we want an image
         to stay in the same column, in the same order, as long
         as that image is on the page, with the exception of
         balancing
         */

        // Remove any images that aren't here any more
        _.each(Object.keys(this.imageColumnLookup), function (imageId) {
            if (this.model.get('imageIds').indexOf(imageId) === -1) {
                myColumn = this.imageColumnLookup[imageId];
                myIndex = this.imageColumns[myColumn].indexOf(imageId);

                this.imageColumns[myColumn].splice(myIndex, 1);
                delete this.imageColumnLookup[imageId];
            }
        }, this);

        // Figure out which new images need placing
        var imagesToPlace = [];

        _.each(Object.keys(this.loadedImages), function (imageId) {
            if (!_.has(this.imageColumnLookup, imageId)) {
                // For some reason, browsers seem to be
                // loading the images backwards. For a
                // better top-down effect (especially
                // when images are fetched in bulk), I'm
                // inserting them at the beginning
                imagesToPlace.splice(0, 0, imageId);
            }
        }, this);

        // Add or remove columns as necessary (images in
        // a dying column need to be placed again)
        while (this.imageColumns.length < numColumns) {
            this.imageColumns.push([]);
        }
        while (this.imageColumns.length > numColumns) {
            var dyingColumn = this.imageColumns.pop();
            if (dyingColumn) {
                _.each(dyingColumn, function (imageId) {
                    delete this.imageColumnLookup[imageId];
                    imagesToPlace.push(imageId);
                }, this);
            }
        }

        // Helper function for placing/balancing
        // columns of images:
        var minAndMaxIndices = _.bind(function () {
            var result = {
                minIndices: [],
                maxIndices: [],
                min: undefined,
                max: undefined,
                minLength: Infinity,
                maxLength: 0
            };

            _.each(this.imageColumns, function (column, index) {
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
        }, this);

        // Consume imagesToPlace by putting images
        // in one of the least-full columns
        while (imagesToPlace.length > 0) {
            imageId = imagesToPlace.pop();
            myColumn = minAndMaxIndices().min;

            this.imageColumns[myColumn].push(imageId);
            this.imageColumnLookup[imageId] = myColumn;
        }

        // Balance the columns
        var minAndMax = minAndMaxIndices();
        while (minAndMax.maxLength - minAndMax.minLength > 3) {
            // Allow a ragged bottom edge... the gap can be as much as 3
            imageId = this.imageColumns[minAndMax.max].pop();
            this.imageColumns[minAndMax.min].push(imageId);
            this.imageColumnLookup[imageId] = minAndMax.min;
            minAndMax = minAndMaxIndices();
        }
    },
    selectImage: function (imageId) {
        if (imageId !== null) {
            this.image.set('_id', imageId);
        } else {
            this.image.clear();
        }
    },
    render: _.debounce(function () {
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
        this.rearrangeColumns(numColumns);

        // Construct a position/height lookup dict
        var placementLookup = {};
        var tallestHeight = 0;
        var availableImages = 0;
        _.each(this.imageColumns, function (column, index) {
            var y = imagePadding;
            _.each(column, function (imageId) {
                // Calculate the natural height of the image
                var height;
                availableImages += 1;
                height = this.imageCache[imageId].height * imageWidth /
                    this.imageCache[imageId].width;
                placementLookup[imageId] = {
                    x: imagePadding + index * (imageWidth + imagePadding),
                    y: y,
                    height: height
                };
                y += height + imagePadding;
            }, this);
            if (y > tallestHeight) {
                tallestHeight = y;
            }
        }, this);

        // After all that, we finally know how much space we need
        svg.attr({
            'width': width,
            'height': tallestHeight
        });

        // Okay, time to draw the pictures (in their initial positions)
        var imageList = Object.keys(this.loadedImages)
            .filter(function (d) {
                return _.has(placementLookup, d);
            });
        var images = svg.select('#previewContents').selectAll('image')
            .data(imageList, function (d) {
                return d;
            });

        // This click callback has to be defined here with a name because it
        // must refer to itself.
        var self = this;
        var click = function (d) {
            // Capture the target element for reference in the nested callback.
            var that = this;

            // This flag and nested callback will detect whether a second click
            // arrives.
            var doubleclick;
            d3.select(that).on('click.second', function () {
                doubleclick = true;
            });

            // This temporarily removes the outer callback from firing (since we
            // don't want to wreck the careful state we're cultivating waiting
            // for a possible second click).
            d3.select(that).on('click', null);

            // Allow 300 ms for a second click to be detected.
            setTimeout(function () {
                // When the 300 ms is up, remove the detector callback and
                // reinstate the main click handler.
                d3.select(that).on('click.second', null);
                d3.select(that).on('click', click);

                // If a double click was detected, then open the full size image
                // in a new window; otherwise, toggle the selection state of the
                // image.
                if (doubleclick) {
                    window.open('/api/v1/image/' + d + '/download?contentDisposition=inline');
                } else {
                    self.selectImage(d === self.image.id ? null : d);
                }
            }, 300);
        };

        images.enter().append('image')
            .attr('preserveAspectRatio', 'xMinYMin');
        images.exit().remove();
        images.attr('id', function (d) {
            return 'image' + d;
        }).attr('xlink:href', _.bind(function (d) {
            return this.imageCache[d].src;
        }, this)).attr('class', _.bind(function (d) {
            if (d === this.image.id) {
                return 'selected';
            } else {
                return null;
            }
        }, this)).attr({
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
        }).on('click', click);

        // Draw the highlight rect
        var selectedImageId = this.image.id;
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

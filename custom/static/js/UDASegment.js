window.UDASegment = function (imageURL, options) {

    var src_image = new Image();
    var tile_image = new Image();

    if (typeof options === 'undefined') {
        options = {};
    }


    function onSourceSuccessLoad(_image, options) {

        tile_image.src = imageURL + "Tiles";
        tile_image.crossOrigin = null;
        tile_image.onerror = function () { onErrorImageLoad(_image); };
        tile_image.onload = function (){ onSuccessImageLoad(_image, tile_image, options); };

    }

    // When image is loaded.
    function onSuccessImageLoad(rgb_image, t_image, options) {

        // create canvas
        var canvas = document.createElement('canvas');
        canvas.width = rgb_image.width;
        canvas.height = rgb_image.height;

        // draw rgb to canvas and grab rgb data
        var context = canvas.getContext('2d');
        context.drawImage(rgb_image, 0, 0);
        var imageData = context.getImageData(0, 0, rgb_image.width, rgb_image.height);
        var rgbData = new Uint8Array(imageData.data);

        // draw tile data to canvas
        context.drawImage(t_image, 0, 0);
        var tileData = context.getImageData(0, 0, t_image.width, t_image.height);

        var sourceData = new Uint8Array(tileData.data);

        var indexMap = new Uint16Array(sourceData.length / 4);

        var numSegments = 0;

        for (var i = 0; i < indexMap.length; i++) {

            // unconvert from multichannel index encoding
            var indexValue = sourceData[i * 4 ] + (256 * sourceData[i * 4 + 1]) + (256 * 256 * sourceData[i * 4 + 2]);

            if (indexValue > numSegments) {
                numSegments = indexValue;
            }

            // copy index to indexmap from Alpha channel
            indexMap[i] = indexValue;
        }

        options.callback({
            width: imageData.width,
            height: imageData.height,
            size: numSegments + 1,
            indexMap: indexMap,
            rgbData: rgbData
        });
    }

    // When image is invalid.
    function onErrorImageLoad(image) {
        alert('Failed to load an image: ' + image.src);
    }

    src_image.src = imageURL + "Source";
    src_image.crossOrigin = null;
    src_image.onerror = function () { onErrorImageLoad(src_image); };
    src_image.onload = function (){ onSourceSuccessLoad(src_image, options); };


};


UDASegmentAnnotator = function (segmentation_url, options) {
    var _this = this;

    UDASegment(segmentation_url, {
        callback: function (result) {
            SegmentAnnotator.call(_this, result, options);
        }
    });

};


UDASegmentAnnotator.prototype = Object.create(SegmentAnnotator.prototype)

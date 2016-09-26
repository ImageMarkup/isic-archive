isic.util.fullscreen = function (id) {
    $('#focusmodal').html(isic.templates.fullscreen());

    var img = $('.focusimage');
    var modal = $('#focusmodal');

    // Supply the image element with a new src attribute to display the image.
    var src = '/api/v1/image/' + id + '/download?contentDisposition=inline';
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
};

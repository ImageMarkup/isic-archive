isic.views.ImagesFacetsPane = isic.View.extend({
    initialize: function () {
        this.facetViews = {};
    },
    render: function () {
        if (!this.addedCollapseImage) {
            // little hack to inject the correct expander image path into the
            // stylesheet (afaik, we can't access girder.staticRoot from the
            // stylus files)
            var isicStylesheet = Array.from(document.styleSheets)
                .filter(function (sheet) {
                    return sheet.href &&
                        sheet.href.indexOf('isic_archive.app.min.css') !== -1;
                })[0];
            isicStylesheet.insertRule('#isic-images-histogramPane ' +
                '.attributeSection .header input.expander:before ' +
                '{background-image: url(' + girder.staticRoot +
                    '/built/plugins/isic_archive/extra/img/collapse.svg);}',
                0);
            this.addedCollapseImage = true;
        }

        _.each(this.facetViews, function (facetView) {
            facetView.destroy();
        }, this);

        this.facetViews = {};
        _.each(_.keys(isic.ENUMS.SCHEMA), function (facetName) {
            var FacetView;
            if (facetName === 'folderId') {
                FacetView = isic.views.ImagesFacetHistogramDatasetView;
            } else {
                FacetView = isic.views.ImagesFacetHistogramView;
            }

            var facetView = new FacetView({
                // TODO: do we want a class?
                // className: '',
                model: this.model,
                facetName: facetName,
                parentView: this
            });

            this.facetViews[facetName] = facetView;
            this.$el.append(facetView.el);
            // Do not render until the view has been inserted into the main DOM
            facetView.render();
        }, this);

        return this;
    }
});

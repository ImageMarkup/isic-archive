/*globals d3*/

isic.views.ImagesViewSubViews = isic.views.ImagesViewSubViews || {};

isic.views.ImagesViewSubViews.HistogramPane = isic.View.extend({
    initialize: function () {
        this.individualHistograms = {};

        this.listenTo(this.model, 'change:overviewHistogram', this.render);
        this.listenTo(this.model, 'change:filteredSetHistogram', this.render);
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

        var attributeOrder = Object.keys(this.model.get('overviewHistogram'))
            .filter(function (d) {
                return isic.ENUMS.SCHEMA[d] && d !== '__passedFilters__' && d !== 'folderId';
            });

        var attributeSections = d3.select(this.el).selectAll('.attributeSection')
            .data(attributeOrder, function (d) {
                return d;
            });
        var attributeSectionsEnter = attributeSections.enter().append('div');
        attributeSections.exit()
            .each(_.bind(function (d) {
                var histogramId = isic.shims.makeValidId(d + '_histogramContent');
                delete this.individualHistograms[histogramId];
            }, this)).remove();
        attributeSections.attr('class', 'attributeSection');

        // Now for the actual histogram content (that gets collapsed)
        var self = this;
        attributeSectionsEnter
            .attr('id', function (d) {
                return isic.shims.makeValidId(d + '_histogramContent');
            })
            .each(function (d) {
                var title;
                if (isic.ENUMS.SCHEMA[d] && isic.ENUMS.SCHEMA[d].humanName) {
                    title = isic.ENUMS.SCHEMA[d].humanName;
                } else {
                    title = d;
                }

                // this refers to the DOM element
                var histogramId = isic.shims.makeValidId(d + '_histogramContent');
                self.individualHistograms[histogramId] =
                    new isic.views.ImagesViewSubViews.IndividualHistogram({
                        el: this,
                        model: self.model,
                        attributeName: d,
                        title: title,
                        parentView: self
                    }).render();
            });
        attributeSections.select('.content').each(_.bind(function (d) {
            var histogramId = isic.shims.makeValidId(d + '_histogramContent');
            // Destroy all tooltips before re-rendering, as a precaution
            $('.tooltip').remove();
            this.individualHistograms[histogramId].render();
        }, this));
        return this;
    }
});

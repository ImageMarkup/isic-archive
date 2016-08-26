/*globals d3*/

isic.views.ImagesViewSubViews = isic.views.ImagesViewSubViews || {};

isic.views.ImagesViewSubViews.HistogramPane = Backbone.View.extend({
    initialize: function () {
        var self = this;

        self.individualHistograms = {};

        self.listenTo(self.model, 'change:overviewHistogram', self.render);
        self.listenTo(self.model, 'change:filteredSetHistogram', self.render);
        self.listenTo(self.model, 'change:pageHistogram', self.render);
    },
    render: function () {
        var self = this;

        if (!self.addedCollapseImage) {
            // little hack to inject the correct expander image path into the
            // stylesheet (afaik, we can't access girder.staticRoot from the
            // stylus files)
            var isicStylesheet = Array.from(document.styleSheets)
                .filter(function (sheet) {
                    return sheet.href &&
                        sheet.href.indexOf('isic_archive.min.css') !== -1;
                })[0];
            isicStylesheet.insertRule('#isic-images-histogramPane ' +
                '.attributeSection .header input.expander:before ' +
                '{background-image: url(' + girder.staticRoot +
                    '/built/plugins/isic_archive/extra/img/collapse.svg);}',
                0);
            self.addedCollapseImage = true;
        }

        var attributeOrder = Object.keys(self.model.get('overviewHistogram'))
            .filter(function (d) {
                return d !== '__passedFilters__' && d !== 'folderId';
            });

        var attributeSections = d3.select(this.el).selectAll('.attributeSection')
            .data(attributeOrder, function (d) {
                return d;
            });
        var attributeSectionsEnter = attributeSections.enter().append('div');
        attributeSections.exit()
            .each(function (d) {
                var histogramId = window.shims.makeValidId(d + '_histogramContent');
                delete self.individualHistograms[histogramId];
            }).remove();
        attributeSections.attr('class', 'attributeSection');

        // Add a container for the stuff in the header (the stuff
        // that is shown while collapsed)
        var sectionHeadersEnter = attributeSectionsEnter.append('div')
            .attr('class', 'header');
        var sectionTitlesEnter = sectionHeadersEnter.append('div')
            .attr('class', 'title');
        var sectionTitles = attributeSections.select('.header')
            .select('.title');

        // Add an arrow to collapse the section
        /*
        This code adds a little triangle to collapse each
        histogram section; this doesn't quite function
        correctly yet... (it's likely something as simple
        as a bad CSS selector)

        sectionTitlesEnter.append('input')
            .attr('type', 'checkbox')
            .attr('class', 'expander');
        sectionTitles.select('input.expander')
            .on('change', function (d) {
                // this refers to the DOM element
                var histogramId = window.shims.makeValidId(d + '_histogramContent');
                var contentElement = self.$el.find('#' + histogramId);
                if (self.checked) {
                    contentElement.removeClass('collapsed');
                    // Update that particular histogram
                    self.individualHistograms[histogramId].render();
                } else {
                    contentElement.addClass('collapsed');
                }
            });
        */

        // Label for the header
        sectionTitlesEnter.append('span');
        sectionTitles.select('span')
            .text(function (d) {
                if (window.ENUMS.SCHEMA[d] &&
                        window.ENUMS.SCHEMA[d].humanName) {
                    return window.ENUMS.SCHEMA[d].humanName;
                } else {
                    return d;
                }
            });

        // Now for the actual histogram content (that gets collapsed)
        attributeSectionsEnter.append('svg')
            .attr('class', 'collapsed content')
            .attr('id', function (d) {
                return window.shims.makeValidId(d + '_histogramContent');
            })
            .each(function (d) {
                // this refers to the DOM element
                var histogramId = window.shims.makeValidId(d + '_histogramContent');
                self.individualHistograms[histogramId] =
                    new isic.views.ImagesViewSubViews.IndividualHistogram({
                        el: this,
                        model: self.model,
                        attributeName: d
                    });
            });
        attributeSections.select('.content').each(function (d) {
            var histogramId = window.shims.makeValidId(d + '_histogramContent');
            self.individualHistograms[histogramId].render();
        });
        return this;
    }
});

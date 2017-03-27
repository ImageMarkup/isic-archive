/*globals d3*/

var ICONS = {
    check: girder.staticRoot + '/built/plugins/isic_archive/extra/img/check.svg',
    ex: girder.staticRoot + '/built/plugins/isic_archive/extra/img/ex.svg',
    dash: girder.staticRoot + '/built/plugins/isic_archive/extra/img/dash.svg'
};

isic.views.ImagesFacetView = isic.View.extend({
    className: 'isic-images-facet',

    /**
     * @param {isic.models.ImagesFacetModel} settings.completeFacet
     * @param {isic.models.ImagesFacetModel} settings.filteredFacet
     * @param {isic.collections.ImagesFilters} settings.filters
     */
    initialize: function (settings) {
        this.completeFacet = settings.completeFacet;
        this.filteredFacet = settings.filteredFacet;
        this.filters = settings.filters;

        this.attrName = this.completeFacet.id;
        this.title = this.completeFacet.schema().title;
    },

    events: {
        'click .toggle': function (evt) {
            this.$('.toggle').toggleClass('icon-down-open')
                .toggleClass('icon-right-open');

            this.$('.isic-images-facet-content').toggle();
        }
    },

    _zipFacetBins: function () {
        return _.map(this.completeFacet.get('bins'), function (completeFacetBin) {
            // TODO: this takes O(n^2); can it be done faster with "_.zip"?
            var filteredFacetBin = _.findWhere(
                this.filteredFacet.get('bins'),
                {label: completeFacetBin.label});
            return {
                completeFacetBin: completeFacetBin,
                filteredFacetBin: filteredFacetBin
            };
        }, this);
    },

    _getBinLabel: function (bin) {
        if (bin.label === null) {
            return 'unknown';
        } else if (_.has(bin, 'lowBound')) {
            var formatter = d3.format('0.3s');
            return bin.label[0] +
                formatter(bin.lowBound) + ' - ' +
                formatter(bin.highBound) +
                bin.label[bin.label.length - 1];
        } else {
            return bin.label;
        }
    },

    _toggleBin: function (binLabel) {
        var binIncluded = this.filters.isIncluded(this.attrName, binLabel);
        this.filters.setIncluded(this.attrName, binLabel, !binIncluded);
    }
});

isic.views.ImagesFacetHistogramView = isic.views.ImagesFacetView.extend({
    /**
     * @param {isic.models.ImagesFacetModel} settings.completeFacet
     * @param {isic.models.ImagesFacetModel} settings.filteredFacet
     * @param {isic.collections.ImagesFilters} settings.filters
     */
    initialize: function (settings) {
        isic.views.ImagesFacetView.prototype.initialize.call(this, settings);

        this.scale = new isic.views.HistogramScale();

        this.listenTo(this.filteredFacet, 'change', this._renderHistogram);
        this.listenTo(this.filters, 'change:' + this.attrName, this._renderHistogram);
    },

    render: function () {
        this.$el.html(isic.templates.imagesFacetHistogram({
            title: this.title,
            staticRoot: girder.staticRoot
        }));
        this._renderHistogram();
    },

    _renderHistogram: function () {
        var svg = d3.select(this.el).select('svg.isic-images-facet-histogram-content');
        if (svg.empty()) {
            // Do nothing until render() has been called
            return;
        }

        var parentWidth = this.el.getBoundingClientRect().width;
        var emSize = parseFloat(svg.style('font-size'));
        this.scale.update(
            this.completeFacet.get('bins'),
            // TODO: this.filteredFacet might not be ready?
            this.filteredFacet.get('bins'),
            emSize, parentWidth);

        var width = this.scale.width;
        var topPadding = 0.5 * emSize;
        var height = this.scale.height + topPadding;

        // Draw the y axis
        var yScale = d3.scale.linear()
            .domain([0, this.scale.yMax])
            .range([height, topPadding]);
        var yAxis = d3.svg.axis()
            .scale(yScale)
            .orient('left')
            .ticks(Math.min(4, this.scale.yMax))
            .tickFormat(d3.format('s'));
        var yAxisObj = svg.select('.yAxis')
            .attr('transform', 'translate(' + this.scale.leftAxisPadding + ',0)')
            .call(yAxis);

        // Move the special buttons into place and attach their events
        this.$('.selectAllBins').hide();
        svg.select('.selectAllBins')
            .attr('transform', 'translate(' +
                (this.scale.leftAxisPadding - 0.5 * emSize) + ',' +
                (height + emSize) + ')');
        svg.select('.selectAll')
            .on('click', function () {
                // TODO: use this
                this.filters.setAllIncluded(this.attrName, true);
            });

        // Draw the bin groups
        var bins = svg.select('.bins').selectAll('.bin')
            .data(this._zipFacetBins(), function (d) {
                // TODO: is a key function needed?
                return d.completeFacetBin.label;
            });
        var binsEnter = bins.enter().append('g')
            .attr('class', 'bin');
        bins.exit().remove();

        // Move the bins horizontally
        bins.attr('transform', _.bind(function (d) {
            // TODO: There should be a better way to do this
            var binNo = _.findIndex(
                this.completeFacet.get('bins'),
                {label: d.completeFacetBin.label}
            );
            return 'translate(' + this.scale.binToPosition(binNo) + ',' + topPadding + ')';
        }, this));

        // Draw one bar for each bin
        binsEnter.append('rect')
            .attr('class', 'overview');
        binsEnter.append('rect')
            .attr('class', 'filteredSet');

        // This bar is the full height of the space allocated to the bars, and
        // marked almost transparent so that it still picks up mouse events - it
        // is used to trigger a tooltip on top of the overview bar showing how
        // many elements are represented.
        binsEnter.append('rect')
            .classed('target', true)
            .style('opacity', 1e-5);
        // Comment out this line to hide the page histogram (1/2):
        // binsEnter.append('rect')
        //     .attr('class', 'page');

        var self = this;

        // Update each bar
        var drawBars = _.bind(function () {
            bins.select('rect.overview')
                .each(function (d) {
                    // this refers to the DOM element
                    d3.select(this)
                        .attr(self.scale.getBinRect(d.completeFacetBin.label, 'overview'));

                    $(this).tooltip({
                        container: 'body',
                        title: function () {
                            var completeCount = d.completeFacetBin.count;

                            // TODO: The API should always send this value
                            var filteredCount = d.filteredFacetBin ? d.filteredFacetBin.count : 0;

                            if (filteredCount === completeCount) {
                                return String(filteredCount);
                            } else {
                                return filteredCount + ' (of ' + completeCount + ')';
                            }
                        }
                    });
                });
            bins.select('rect.filteredSet')
                .each(function (d) {
                    // this refers to the DOM element
                    d3.select(this)
                      .attr(self.scale.getBinRect(d.completeFacetBin.label, 'filteredSet'));
                });
            bins.select('rect.target')
                .each(function (d) {
                    // this refers to the DOM element

                    var el = d3.select(this.parentElement)
                        .select('rect.overview')
                        .node();

                    // Delegate "mouseover" events to the tooltip on the
                    // overview bar (so that it appears on top of the bar
                    // itself, not at the top of the bar space).
                    d3.select(this)
                      .attr(self.scale.getFullRect())
                      .on('mouseenter', function () {
                          $(el).tooltip('show');
                      })
                      .on('mouseleave', function () {
                          $(el).tooltip('hide');
                      });
                });
            // Comment out these lines to hide the page histogram (2/2):
            // bins.select('rect.page')
            //     .each(function (d) {
            //         // this refers to the DOM element
            //         d3.select(this).attr(self.scale.getBinRect(d.label, 'page'));
            //     });
        }, this);
        drawBars();

        // Add the scale adjustment knob (needs a distinct scale instance)
        var knobScale = yScale.copy();
        var knob = svg.select('.yAxisKnob')
            .attr('transform', 'translate(' +
                this.scale.leftAxisPadding + ',' +
                knobScale(this.scale.yMax) + ')');
        knob.call(d3.behavior.drag()
            .origin(_.bind(function () {
                return { x: 0, y: knobScale(this.scale.yMax) };
            }, this)).on('drag', _.bind(function () {
                // the yMax setter automagically prevents bad values...
                this.scale.yMax = knobScale.invert(d3.event.y);

                // update everything that cares about the y this.scale:
                // the knob
                knob.attr('transform', 'translate(' +
                    this.scale.leftAxisPadding + ',' +
                    knobScale(this.scale.yMax) + ')');
                // the axis
                yScale.domain([0, this.scale.yMax]);
                yAxis.scale(yScale).ticks(Math.min(4, this.scale.yMax));
                yAxisObj.call(yAxis);
                // and the bars
                drawBars();
            }, this)).on('dragstart', function () {
                svg.style('cursor', 'ns-resize');
            }).on('dragend', function () {
                svg.style('cursor', null);
            }));

        // Add an include / exclude button for each bin
        binsEnter.append('image')
            .attr('class', 'button')
            .attr({
                x: -0.5 * emSize,
                y: height + 0.5 * emSize,
                width: emSize,
                height: emSize
            });

        bins.select('image.button')
            .attr('xlink:href', _.bind(function (d) {
                var status = this.filters.isIncluded(this.attrName, d.completeFacetBin.label);

                if (status === true) {
                    return ICONS.check;
                } else if (status === false) {
                    return ICONS.ex;
                } else {
                    // TODO: this should never happen, until we implement continuous filters
                    // or perhaps if the completeFacetBin.count == 0
                    return ICONS.dash;
                }
            }, this))
            .on('click', _.bind(function (d) {
                this._toggleBin(d.completeFacetBin.label);
            }, this));

        height += 2 * emSize;

        // Add each bin label, and compute the total needed height
        var offsetY = 0.25 * emSize;
        var transformHeight = height + offsetY;
        var transformAngle = -45;
        var transformAngleRadians = transformAngle * (Math.PI / 180);
        var maxBoxHeight = svg.select('.selectAllBins').select('text')
            .node().getComputedTextLength();
        binsEnter.append('text');
        bins.select('text')
            .text(_.bind(function (d) {
                return this._getBinLabel(d.completeFacetBin);
            }, this))
            .attr('text-anchor', 'end')
            .attr('transform', 'translate(0 ' + transformHeight + ') rotate(' + transformAngle + ')')
            .each(function (d) {
                // "this" refers to the DOM element

                // Shorten any labels that are too long. Remove letters from the
                // end of the string one by one, and replace with an HTML
                // ellipsis, until the string is a manageable length.
                var me = d3.select(this);
                var text = me.text();
                var shortened = false;
                while (this.getComputedTextLength() > 95) {
                    shortened = true;

                    text = text.slice(0, -1);
                    me.html(text + '&hellip;');
                }

                // Add a tooltip to shortened labels, containing the full label.
                if (shortened) {
                    $(this).tooltip({
                        container: 'body',
                        title: function () {
                            return self._getBinLabel(d.completeFacetBin);
                        }
                    });
                }

                var boxHeight = Math.abs(this.getComputedTextLength() * Math.sin(transformAngleRadians));
                maxBoxHeight = Math.max(boxHeight, maxBoxHeight);
            });
        height += maxBoxHeight + topPadding + offsetY;

        svg.attr({
            width: width + 'px',
            height: height + 'px'
        });
        return this;
    },

    destroy: function () {
        // Since the tooltips are attached to the HTML <body> (way outside the
        // scope of this view's element, just destroy all tooltip elements
        // globally; this is overkill, but can be fixed in a future refactor
        $('.tooltip').remove();

        isic.views.ImagesFacetView.prototype.destroy.call(this);
    }
});

isic.views.ImagesFacetHistogramDatasetView = isic.views.ImagesFacetHistogramView.extend({
    /**
     * @param {isic.models.ImagesFacetModel} settings.completeFacet
     * @param {isic.models.ImagesFacetModel} settings.filteredFacet
     * @param {isic.collections.ImagesFilters} settings.filters
     */
    initialize: function (settings) {
        isic.views.ImagesFacetHistogramView.prototype.initialize.call(this, settings);

        this.datasetCollection = new isic.collections.DatasetCollection();
        this.datasetCollection.once('g:changed', _.bind(function () {
            this._renderHistogram();
        }, this)).fetch({
            limit: 0
        });
    },

    _getBinLabel: function (facetBin) {
        var datasetModel = this.datasetCollection.findWhere({
            _id: facetBin.label
        });
        return datasetModel ? datasetModel.name() : facetBin.label;
    }
});

isic.views.ImagesFacetCategoricalView = isic.views.ImagesFacetView.extend({
    events: function () {
        return _.extend({}, isic.views.ImagesFacetView.prototype.events, {
            'click .isic-images-facet-bin': function (event) {
                var binElem = event.currentTarget;
                var binLabel = d3.select(binElem).datum().completeFacetBin.label;
                this._toggleBin(binLabel);
            }
        });
    },

    /**
     * @param {isic.models.ImagesFacetModel} settings.completeFacet
     * @param {isic.models.ImagesFacetModel} settings.filteredFacet
     * @param {isic.collections.ImagesFilters} settings.filters
     */
    initialize: function (settings) {
        isic.views.ImagesFacetView.prototype.initialize.call(this, settings);

        this.listenTo(this.filteredFacet, 'change', this._rerenderCounts);
        this.listenTo(this.filters, 'change:' + this.attrName, this._rerenderSelections);
    },

    render: function () {
        var completeFacetBins = this.completeFacet.get('bins');

        this.$el.html(isic.templates.imagesFacetCategorical({
            title: this.title,
            bins: completeFacetBins,
            getBinLabel: this._getBinLabel
        }));

        d3.select(this.el).selectAll('.isic-images-facet-bin')
            .data(this._zipFacetBins());
        this._rerenderCounts();
        this._rerenderSelections();
    },

    _rerenderCounts: function () {
        var binElems = d3.select(this.el).selectAll('.isic-images-facet-bin');

        // Don't selectAll to 'isic-images-facet-bin-count' directly, so data is propagated
        binElems.select('.isic-images-facet-bin-count')
            .text(_.bind(function (d) {
                var completeCount = d.completeFacetBin.count;

                // TODO: The API should always send this value
                var filteredCount = d.filteredFacetBin ? d.filteredFacetBin.count : 0;

                var label;
                if (completeCount === filteredCount) {
                    label = completeCount;
                } else {
                    label = filteredCount + ' / ' + completeCount;
                }
                return '(' + label + ')';
            }, this));
    },

    _rerenderSelections: function () {
        var binElems = d3.select(this.el).selectAll('.isic-images-facet-bin');

        // Don't selectAll to 'isic-images-facet-bin-count' directly, so data is propagated
        // TODO: can this be done in a single pass?
        binElems.select('i')
            .classed('icon-check', _.bind(function (d) {
                return this.filters.isIncluded(this.attrName, d.completeFacetBin.label);
            }, this))
            .classed('icon-check-empty', _.bind(function (d) {
                return !this.filters.isIncluded(this.attrName, d.completeFacetBin.label);
            }, this));
    }
});
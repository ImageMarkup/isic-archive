/*globals d3*/

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

        this.facetId = this.completeFacet.id;
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
        // TODO: This whole function would be unnecessary if "this.filteredFacet.get('bins')" were
        // not totally reset on every fetch, but had empty bins just set to 0
        var filteredBins = this.filteredFacet.get('bins');
        var filteredBinsIter = 0;
        return _.map(this.completeFacet.get('bins'), function (completeBin) {
            // Since both completeBin and filteredBin are sorted by label, we can do this much more
            // efficiently in O(n), than if we used "_.findWhere" in O(n^2)

            var filteredBin;
            var possibleFilteredBin = filteredBins[filteredBinsIter];
            // It's possible for "filteredBinsIter" to overrun "filteredBins" (if the last bins are
            // excluded), so check that "possibleFilteredBin" exists
            if (possibleFilteredBin && completeBin.label === possibleFilteredBin.label) {
                filteredBin = possibleFilteredBin;
                filteredBinsIter++;
            } else {
                filteredBin = {
                    label: completeBin.label,
                    count: 0
                };
            }
            return {
                completeBin: completeBin,
                filteredBin: filteredBin
            };
        }, this);
    },

    _getBinTitle: function (completeBin) {
        if (completeBin.label === '__null__') {
            return 'unknown';
        } else if (_.has(completeBin, 'lowBound')) {
            var formatter = d3.format('0.3s');
            return completeBin.label[0] +
                formatter(completeBin.lowBound) + ' - ' +
                formatter(completeBin.highBound) +
                completeBin.label[completeBin.label.length - 1];
        } else {
            return completeBin.label;
        }
    },

    _toggleBin: function (binLabel) {
        var binIncluded = this.filters.isIncluded(this.facetId, binLabel);
        this.filters.setIncluded(this.facetId, binLabel, !binIncluded);
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
        this.listenTo(this.filters, 'change:' + this.facetId, this._renderHistogram);
    },

    render: function () {
        this.$el.html(isic.templates.imagesFacetHistogram({
            title: this.title,
            staticImageRoot: girder.staticRoot + '/built/plugins/isic_archive/extra/img'
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
                this.filters.setAllIncluded(this.facetId, true);
            });

        // Draw the bin groups
        var bins = svg.select('.bins').selectAll('.bin')
            .data(this._zipFacetBins(), function (d) {
                // TODO: is a key function needed?
                return d.completeBin.label;
            });
        var binsEnter = bins.enter().append('g')
            .attr('class', 'bin');
        bins.exit().remove();

        // Move the bins horizontally
        bins.attr('transform', _.bind(function (d) {
            // TODO: There should be a better way to do this
            var binNo = _.findIndex(
                this.completeFacet.get('bins'),
                {label: d.completeBin.label}
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
                        .attr(self.scale.getBinRect(d.completeBin.label, 'overview'));

                    $(this).tooltip({
                        container: 'body',
                        title: function () {
                            var completeCount = d.completeBin.count;
                            var filteredCount = d.filteredBin.count;
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
                      .attr(self.scale.getBinRect(d.completeBin.label, 'filteredSet'));
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
            //         d3.select(this).attr(self.scale.getBinRect(d.completeBin.label, 'page'));
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
                var status = this.filters.isIncluded(this.facetId, d.completeBin.label);

                var staticImageRoot = girder.staticRoot + '/built/plugins/isic_archive/extra/img';
                if (status === true) {
                    return staticImageRoot + '/check.svg';
                } else if (status === false) {
                    return staticImageRoot + '/ex.svg';
                } else {
                    // TODO: this should never happen, until we implement continuous filters
                    // or perhaps if the completeFacetBin.count == 0
                    return staticImageRoot + '/dash.svg';
                }
            }, this))
            .on('click', _.bind(function (d) {
                this._toggleBin(d.completeBin.label);
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
                return this._getBinTitle(d.completeBin);
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

                // Add a tooltip to shortened labels, containing the full title.
                if (shortened) {
                    $(this).tooltip({
                        container: 'body',
                        title: function () {
                            return self._getBinTitle(d.completeBin);
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

    _getBinTitle: function (completeBin) {
        var datasetModel = this.datasetCollection.get(completeBin.label);
        return datasetModel ? datasetModel.name() : completeBin.label;
    }
});

isic.views.ImagesFacetCategoricalView = isic.views.ImagesFacetView.extend({
    events: function () {
        return _.extend({}, isic.views.ImagesFacetView.prototype.events, {
            'click .isic-images-facet-bin': function (event) {
                var binElem = this.$(event.currentTarget);
                var binLabel = binElem.data('binLabel');
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
        this.listenTo(this.filters, 'change:' + this.facetId, this._rerenderSelections);
    },

    render: function () {
        this.$el.html(isic.templates.imagesFacetCategorical({
            title: this.title,
            bins: this.completeFacet.get('bins'),
            getBinTitle: this._getBinTitle
        }));

        this._rerenderCounts();
        this._rerenderSelections();
    },

    _rerenderCounts: function () {
        // Both countElems and binVals are guaranteed to be in corresponding order, as they are
        // both created from the same completeBin (and jQuery returns elements in the order on the
        // DOM)
        var countElems = this.$('.isic-images-facet-bin>.isic-images-facet-bin-count');
        var binVals = this._zipFacetBins();
        _.each(_.zip(countElems, binVals), _.bind(function (arg) {
            var countElem = this.$(arg[0]);
            var binVal = arg[1];

            var completeCount = binVal.completeBin.count;
            var filteredCount = binVal.filteredBin.count;
            var label;
            if (filteredCount === completeCount) {
                label = completeCount;
            } else {
                label = filteredCount + ' / ' + completeCount;
            }
            label = '(' + label + ')';

            countElem.text(label);
        }, this));
    },

    _rerenderSelections: function () {
        this.$('.isic-images-facet-bin').each(_.bind(function (index, binElem) {
            var jqBinElem = this.$(binElem);
            var checkElem = jqBinElem.find('i');
            var binLabel = jqBinElem.data('binLabel');
            var binIncluded = this.filters.isIncluded(this.facetId, binLabel);
            checkElem
                .toggleClass('icon-check', binIncluded)
                .toggleClass('icon-check-empty', !binIncluded);
        }, this));
    }
});

/*globals d3*/

var ICONS = {
    check: girder.staticRoot + '/built/plugins/isic_archive/extra/img/check.svg',
    ex: girder.staticRoot + '/built/plugins/isic_archive/extra/img/ex.svg',
    dash: girder.staticRoot + '/built/plugins/isic_archive/extra/img/dash.svg'
};

isic.views.ImagesFacetView = isic.View.extend({
    className: 'isic-images-facet',

    initialize: function (parameters) {
        this.attrName = parameters.facetName;

        this.attrType = this.model.getAttributeType(this.attrName);
        this.title = isic.ENUMS.SCHEMA[this.attrName].humanName;
    },

    events: {
        'click .toggle': function (evt) {
            this.$('.toggle').toggleClass('icon-down-open')
                .toggleClass('icon-right-open');

            this.$('.isic-images-facet-content').toggle();
        }
    },

    _getFieldLabel: function (fieldInfo) {
        if (fieldInfo.label === null) {
            return 'unknown';
        } else if (_.has(fieldInfo, 'lowBound')) {
            var formatter = d3.format('0.3s');
            return fieldInfo.label[0] +
                formatter(fieldInfo.lowBound) + ' - ' +
                formatter(fieldInfo.highBound) +
                fieldInfo.label[fieldInfo.label.length - 1];
        } else {
            return fieldInfo.label;
        }
    },

    _toggleBin: function (bin) {
        var status = this.model.getBinStatus(this.attrName, bin);

        // To add / remove ranges, we might need to provide a comparison
        // function (undefined will just do default comparisons)
        var comparator;
        if (this.attrType === 'string') {
            comparator = function (a, b) {
                return a.localeCompare(b);
            };
        }

        // TODO: Ideally, this should select and cancel only the old
        // set of requests (and could be called in
        // ImagesViewModel.updateFilters); until that's fixed,
        // hopefully nobody will click histogram buttons too early
        // in the page load
        girder.cancelRestRequests();

        if (status === isic.ENUMS.BIN_STATES.INCLUDED) {
            // Remove this bin
            if (_.has(bin, 'lowBound') && _.has(bin, 'highBound')) {
                this.model.removeRange(
                    this.attrName, bin.lowBound, bin.highBound, comparator);
            } else {
                this.model.removeValue(this.attrName, bin.label);
            }
        } else {
            // Add this bin
            if (_.has(bin, 'lowBound') && _.has(bin, 'highBound')) {
                this.model.includeRange(
                    this.attrName, bin.lowBound, bin.highBound, comparator);
            } else {
                this.model.includeValue(this.attrName, bin.label);
            }
        }
    }
});

isic.views.ImagesFacetHistogramView = isic.views.ImagesFacetView.extend({
    initialize: function (parameters) {
        isic.views.ImagesFacetView.prototype.initialize.call(this, parameters);

        this.scale = new isic.views.ImagesViewSubViews.HistogramScale();

        this.listenTo(this.model, 'change:overviewHistogram', this._renderHistogram);
        this.listenTo(this.model, 'change:filteredSetHistogram', this._renderHistogram);
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
            this.model.get('overviewHistogram')[this.attrName],
            this.model.get('filteredSetHistogram')[this.attrName],
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
                this.model.clearFilters(this.attrName);
            });

        // Draw the bin groups
        var bins = svg.select('.bins').selectAll('.bin')
            .data(this.scale.overviewHistogram, function (d) {
                return d.label;
            });
        var binsEnter = bins.enter().append('g')
            .attr('class', 'bin');
        bins.exit().remove();

        // Move the bins horizontally
        bins.attr('transform', _.bind(function (d) {
            var binNo = _.findIndex(
                this.model.get('overviewHistogram')[this.attrName],
                {label: d.label}
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
                        .attr(self.scale.getBinRect(d.label, 'overview'));

                    $(this).tooltip({
                        container: 'body',
                        title: function () {
                            var overviewCount = d.count;

                            var filteredBin = _.findWhere(
                                self.model.get('filteredSetHistogram')[self.attrName],
                                {label: d.label}
                            );
                            var filteredCount = filteredBin ? filteredBin.count : 0;

                            if (filteredCount === overviewCount) {
                                return String(filteredCount);
                            } else {
                                return filteredCount + ' (of ' + overviewCount + ')';
                            }
                        }
                    });
                });
            bins.select('rect.filteredSet')
                .each(function (d) {
                    // this refers to the DOM element
                    d3.select(this)
                      .attr(self.scale.getBinRect(d.label, 'filteredSet'));
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
                var status = this.model.getBinStatus(this.attrName, d);

                if (status === isic.ENUMS.BIN_STATES.INCLUDED) {
                    return ICONS.check;
                } else if (status === isic.ENUMS.BIN_STATES.EXCLUDED) {
                    return ICONS.ex;
                } else {
                    return ICONS.dash;
                }
            }, this))
            .on('click', _.bind(function (d) {
                var bin = d;
                this._toggleBin(bin);
                this._renderHistogram();
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
            .text(_.bind(this._getFieldLabel, this))
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
                            return self._getFieldLabel(d);
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
    _getFieldLabel: function (fieldInfo) {
        return this.model.datasetCollection.findWhere({
            _id: fieldInfo.label
        }).name();
    }
});

isic.views.ImagesFacetCategoricalView = isic.views.ImagesFacetView.extend({
    events: function () {
        return _.extend({}, isic.views.ImagesFacetView.prototype.events, {
            'click .isic-images-facet-bin': function (event) {
                var binElem = event.currentTarget;

                this.$(binElem).find('i')
                    .toggleClass('icon-check')
                    .toggleClass('icon-check-empty');

                var bin = d3.select(binElem).datum();
                this._toggleBin(bin);
            }
        });
    },

    initialize: function (parameters) {
        isic.views.ImagesFacetView.prototype.initialize.call(this, parameters);

        this.listenTo(this.model, 'change:overviewHistogram', this.render);
        this.listenTo(this.model, 'change:filteredSetHistogram', this._rerenderCounts);
    },

    render: function () {
        var overviewBins = this.model.get('overviewHistogram')[this.attrName];

        this.$el.html(isic.templates.imagesFacetCategorical({
            title: this.title,
            bins: overviewBins || []
        }));
        if (!overviewBins) {
            return;
        }

        var binElems = d3.select(this.el).selectAll('.isic-images-facet-bin')
            .data(overviewBins);
        binElems.select('.isic-images-facet-bin-name')
            .text(_.bind(this._getFieldLabel, this));

        this._rerenderCounts();
    },

    _rerenderCounts: function () {
        var binElems = d3.select(this.el).selectAll('.isic-images-facet-bin');

        var filteredBins = this.model.get('filteredSetHistogram')[this.attrName];
        // Don't selectAll to 'isic-images-facet-bin-count' directly, so data is propagated
        binElems.select('.isic-images-facet-bin-count')
            .text(_.bind(function (d) {
                var overviewCount = d.count;

                var filteredSetBin = _.findWhere(filteredBins, {label: d.label});
                var filteredSetCount = filteredSetBin ? filteredSetBin.count : 0;

                var label;
                if (overviewCount === filteredSetCount) {
                    label = overviewCount;
                } else {
                    label = filteredSetCount + ' / ' + overviewCount;
                }
                return '(' + label + ')';
            }, this));
    }
});

/*globals d3*/

var ICONS = {
    check: girder.staticRoot + '/built/plugins/isic_archive/extra/img/check.svg',
    ex: girder.staticRoot + '/built/plugins/isic_archive/extra/img/ex.svg',
    dash: girder.staticRoot + '/built/plugins/isic_archive/extra/img/dash.svg'
};

isic.views.ImagesFacetView = isic.View.extend({
});

isic.views.ImagesFacetHistogramView = isic.views.ImagesFacetView.extend({
    events: {
        'click .toggle': function (evt) {
            this.$('.toggle').toggleClass('icon-down-open')
                .toggleClass('icon-right-open');

            this.$('svg.content').toggle();
        }
    },
    initialize: function (parameters) {
        this.attrName = parameters.attributeName;

        this.title = isic.ENUMS.SCHEMA[this.attrName].humanName;

        this.scale = new isic.views.ImagesViewSubViews.HistogramScale(this.attrName);
    },
    render: function () {
        this.$el.html(isic.templates.individualHistogram({
            title: this.title
        }));

        var svg = d3.select(this.el).select('svg.content');

        var parentWidth = this.el.getBoundingClientRect().width;
        var emSize = parseFloat(this.$('svg').css('font-size'));
        this.scale.update(this.model, emSize, parentWidth);

        var width = this.scale.width;
        var topPadding = 0.5 * emSize;
        var height = this.scale.height + topPadding;

        svg.html(isic.templates.imagesPageHistogram({
            staticRoot: girder.staticRoot
        }));

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
            var binNo = this.scale.labelToBin(d.label, 'overview');
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

        // Update each bar
        var drawBars = _.bind(function () {
            var self = this;
            bins.select('rect.overview')
                .each(function (d) {
                    // this refers to the DOM element
                    d3.select(this)
                        .attr(self.scale.getBinRect(d.label, 'overview'));

                    $(this).tooltip({
                        container: 'body',
                        title: function () {
                            var overviewCount = self.scale.labelToCount(d.label, 'overview');
                            var filteredCount = self.scale.labelToCount(d.label, 'filteredSet');

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
        var self = this;
        bins.select('image.button').each(function (d) {
            // this refers to the DOM element
            var bin = self.scale.labelToBin(d.label, 'overview');
            bin = self.model.get('overviewHistogram')[self.attrName][bin];
            var status = self.model.getBinStatus(self.attrName, bin);

            // To add / remove ranges, we might need to provide a comparison
            // function (undefined will just do default comparisons)
            var comparator;
            if (self.model.getAttributeType(self.attrName) === 'string') {
                comparator = function (a, b) {
                    return a.localeCompare(b);
                };
            }

            d3.select(this)
                .attr('xlink:href', function () {
                    if (status === isic.ENUMS.BIN_STATES.INCLUDED) {
                        return ICONS.check;
                    } else if (status === isic.ENUMS.BIN_STATES.EXCLUDED) {
                        return ICONS.ex;
                    } else {
                        return ICONS.dash;
                    }
                }).on('click', function (d) {
                    if (status === isic.ENUMS.BIN_STATES.INCLUDED) {
                        // Remove this bin
                        if (bin.hasOwnProperty('lowBound') &&
                                bin.hasOwnProperty('highBound')) {
                            self.model.removeRange(self.attrName,
                                bin.lowBound, bin.highBound, comparator);
                        } else {
                            self.model.removeValue(self.attrName, bin.label);
                        }
                    } else {
                        // Add this bin
                        if (bin.hasOwnProperty('lowBound') &&
                                bin.hasOwnProperty('highBound')) {
                            self.model.includeRange(self.attrName,
                                bin.lowBound, bin.highBound, comparator);
                        } else {
                            self.model.includeValue(self.attrName, bin.label);
                        }
                    }

                    self.render();
                });
        });
        height += 2 * emSize;

        // Add each bin label, and compute the total needed height
        var offsetY = 0.25 * emSize;
        var transformHeight = height + offsetY;
        var transformAngle = -45;
        var transformAngleRadians = transformAngle * (Math.PI / 180);
        var maxBoxHeight = svg.select('.selectAllBins').select('text')
            .node().getComputedTextLength();
        binsEnter.append('text');
        var formatter = d3.format('0.3s');
        bins.select('text')
            .text(_.bind(function (d) {
                var label;
                if (this.attrName === 'folderId') {
                    label = this.model.datasetCollection.findWhere({
                        _id: d.label
                    }).name();
                } else if (d.label === 'NaN' || d.label === 'undefined') {
                    label = 'unknown';
                } else if (_.has(d, 'lowBound')) {
                    label = d.label[0] + formatter(d.lowBound) + ' - ' +
                        formatter(d.highBound) + d.label[d.label.length - 1];
                } else {
                    label = d.label;
                }
                return label;
            }, this))
            .attr('text-anchor', 'end')
            .attr('transform', 'translate(0 ' + transformHeight + ') rotate(' + transformAngle + ')')
            .each(function () {
                // this refers to the DOM element
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
});

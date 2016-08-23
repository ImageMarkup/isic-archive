isic.views.ImagesViewSubViews = isic.views.ImagesViewSubViews || {};

var ICONS = {
    check: girder.staticRoot + '/built/plugins/isic_archive/extra/img/check.svg',
    ex: girder.staticRoot + '/built/plugins/isic_archive/extra/img/ex.svg',
    dash: girder.staticRoot + '/built/plugins/isic_archive/extra/img/dash.svg'
};

var MODEL_ENUMS;

isic.views.ImagesViewSubViews.IndividualHistogram = Backbone.View.extend({
    initialize: function (parameters) {
        var self = this;
        self.attrName = parameters.attributeName;
        self.scale = new isic.views.ImagesViewSubViews
            .HistogramScale(self.attrName);
    },
    render: function () {
        var self = this;
        var parentWidth = this.el.parentNode.getBoundingClientRect().width;
        var emSize = parseFloat(self.$el.css('font-size'));
        self.scale.update(self.model, emSize, parentWidth);

        var svg = d3.select(self.el);
        var width = self.scale.width;
        var topPadding = 0.5 * emSize;
        var height = self.scale.height + topPadding;

        if (!self.addedTemplate) {
            svg.html(isic.templates.imagesPageHistogram({
                staticRoot: girder.staticRoot
            }));
            self.addedTemplate = true;
        }

        // Draw the y axis
        var yScale = d3.scale.linear()
            .domain([0, self.scale.yMax])
            .range([height, topPadding]);
        var yAxis = d3.svg.axis()
            .scale(yScale)
            .orient('left')
            .ticks(Math.min(4, self.scale.yMax))
            .tickFormat(d3.format('0.3s'));
        var yAxisObj = svg.select('.yAxis')
            .attr('transform', 'translate(' + self.scale.leftAxisPadding + ',0)')
            .call(yAxis);

        // Move the special buttons into place and attach their events
        svg.select('.selectAllBins')
            .attr('transform', 'translate(' +
                (self.scale.leftAxisPadding - 0.5 * emSize) + ',' +
                (height + emSize) + ')');
        svg.select('.selectAll')
            .on('click', function () {
                self.model.clearFilters(self.attrName);
            });

        // Draw the bin groups
        var labels = self.scale.overviewHistogram.map(function (d) {
            return d.label;
        });
        var bins = svg.select('.bins').selectAll('.bin')
            .data(labels, function (d) {
                return d;
            });
        var binsEnter = bins.enter().append('g')
            .attr('class', 'bin');
        bins.exit().remove();

        // Move the bins horizontally
        bins.attr('transform', function (d) {
            var binNo = self.scale.labelToBin(d, 'overview');
            return 'translate(' + self.scale.binToPosition(binNo) + ',' + topPadding + ')';
        });

        // Draw one bar for each bin
        binsEnter.append('rect')
            .attr('class', 'overview');
        binsEnter.append('rect')
            .attr('class', 'filteredSet');
        binsEnter.append('rect')
            .attr('class', 'page');

        // Update each bar
        function drawBars () {
            bins.select('rect.overview')
                .each(function (d) {
                    // this refers to the DOM element
                    d3.select(this).attr(self.scale.getBinRect(d, 'overview'));
                });
            bins.select('rect.filteredSet')
                .each(function (d) {
                    // this refers to the DOM element
                    d3.select(this).attr(self.scale.getBinRect(d, 'filteredSet'));
                });
            bins.select('rect.page')
                .each(function (d) {
                    // this refers to the DOM element
                    d3.select(this).attr(self.scale.getBinRect(d, 'page'));
                });
        }
        drawBars();

        // Add the scale adjustment knob (needs a distinct scale instance)
        var knobScale = yScale.copy();
        var knob = svg.select('.yAxisKnob')
            .attr('transform', 'translate(' +
                self.scale.leftAxisPadding + ',' +
                knobScale(self.scale.yMax) + ')');
        knob.call(d3.behavior.drag()
            .origin(function () {
                return { x: 0, y: knobScale(scale.yMax) };
            }).on('drag', function () {
                // the yMax setter automagically prevents bad values...
                self.scale.yMax = knobScale.invert(d3.event.y);

                // update everything that cares about the y self.scale:
                // the knob
                knob.attr('transform', 'translate(' +
                    self.scale.leftAxisPadding + ',' +
                    knobScale(scale.yMax) + ')');
                // the axis
                yScale.domain([0, self.scale.yMax]);
                yAxis.scale(yScale).ticks(Math.min(4, self.scale.yMax));
                yAxisObj.call(yAxis);
                // and the bars
                drawBars();
            }).on('dragstart', function () {
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
        bins.select('image.button').each(function (d) {
            // this refers to the DOM element
            var bin = self.scale.labelToBin(d, 'overview');
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
                    if (status === window.ENUMS.BIN_STATES.INCLUDED) {
                        return ICONS.check;
                    } else if (status === window.ENUMS.BIN_STATES.EXCLUDED) {
                        return ICONS.ex;
                    } else {
                        return ICONS.dash;
                    }
                }).on('click', function (d) {
                    if (status === window.ENUMS.BIN_STATES.INCLUDED) {
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
                });
            });
        height += 2 * emSize;

        // Add each bin label, and compute the total needed height
        window.test = svg;
        var maxLabelHeight = svg.select('.selectAllBins').select('text')
            .node().getComputedTextLength();
        binsEnter.append('text');
        bins.select('text')
            .text(function (d) {
                return d;
            })
            .attr('transform', 'rotate(90) translate(' + height + ',' +
                (0.35 * emSize) + ')')
            .each(function () {
                // this refers to the DOM element
                maxLabelHeight = Math.max(this.getComputedTextLength(), maxLabelHeight);
            });
        height += maxLabelHeight + topPadding;

        svg.attr({
            width: width + 'px',
            height: height + 'px'
        });
        return this;
    }
});

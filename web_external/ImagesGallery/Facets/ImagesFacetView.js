import d3 from 'd3';
import $ from 'jquery';
import _ from 'underscore';
import 'bootstrap/js/tooltip';

import {CategoricalFacetFilter, IntervalFacetFilter, TagsCategoricalFacetFilter} from '../ImagesFilter';
import DatasetCollection from '../../collections/DatasetCollection';
import View from '../../view';

import HistogramScale from './HistogramScale';

/* eslint-disable import/order */
import ImagesFacetHistogramTemplate from './imagesFacetHistogram.pug';
import ImagesFacetCategoricalTemplate from './imagesFacetCategorical.pug';
import checkImageUrl from '!url-loader!svg-fill-loader!./check.svg?fill=#999999'; // eslint-disable-line import/no-webpack-loader-syntax
import dashImageUrl from '!url-loader!svg-fill-loader!./dash.svg?fill=#999999'; // eslint-disable-line import/no-webpack-loader-syntax
import exImageUrl from '!url-loader!svg-fill-loader!./ex.svg?fill=#999999'; // eslint-disable-line import/no-webpack-loader-syntax
/* eslint-enable import/order */

const ImagesFacetView = View.extend({
    className: 'isic-images-facet',

    events: {
        'show.bs.collapse .isic-images-facet-content': '_toggleCollapseIndicator',
        'hide.bs.collapse .isic-images-facet-content': '_toggleCollapseIndicator'
    },

    /**
     * @param {ImagesFacetModel} settings.completeFacet
     * @param {ImagesFacetModel} settings.filteredFacet
     * @param {ImagesFilter} settings.filter
     */
    initialize: function (settings) {
        this.completeFacet = settings.completeFacet;
        this.filteredFacet = settings.filteredFacet;
        this.filter = settings.filter;

        this.facetId = this.completeFacet.id;
        this.facetContentId = `${this.className}-${this.facetId.replace(/\./g, '-')}`;
        this.title = this.completeFacet.schema().title;
    },

    _toggleCollapseIndicator: function () {
        this.$('.isic-images-facet-indicator')
            .toggleClass('icon-down-open')
            .toggleClass('icon-right-open');
    },

    /**
     * Apply initial collapse state defined in schema.
     */
    _applyInitialCollapseState: function () {
        let schema = this.completeFacet.schema();
        if (schema.collapsed) {
            this.$('.isic-images-facet-content.collapse').collapse('hide');
        }
    },

    _zipFacetBins: function () {
        // TODO: This whole function would be unnecessary if "this.filteredFacet.get('bins')" were
        // not totally reset on every fetch, but had empty bins just set to 0
        let filteredBins = this.filteredFacet.get('bins');
        let filteredBinsIter = 0;
        return _.map(this.completeFacet.get('bins'), (completeBin) => {
            // Since both completeBin and filteredBin are sorted by label, we can do this much more
            // efficiently in O(n), than if we used "_.findWhere" in O(n^2)

            let filteredBin;
            let possibleFilteredBin = filteredBins[filteredBinsIter];
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
        });
    },

    _getBinTitle: function (completeBin) {
        if (completeBin.label === '__null__') {
            return 'unknown';
        } else if (_.has(completeBin, 'lowBound')) {
            // Decimal notation, rounded to significant digits
            let formatter = d3.format('0.3r');
            let lowBracket = completeBin.label[0];
            let highBracket = completeBin.label[completeBin.label.length - 1];
            let lowBound = formatter(completeBin.lowBound);
            let highBound = formatter(completeBin.highBound);
            return `${lowBracket}${lowBound} - ${highBound}${highBracket}`;
        } else {
            return completeBin.label;
        }
    },

    _toggleBin: function (binLabel) {
        let binIncluded = this.filter.isIncluded(binLabel);
        this.filter.setIncluded(binLabel, !binIncluded);
    }
});

const ImagesFacetHistogramView = ImagesFacetView.extend({
    events: function () {
        return _.extend({}, ImagesFacetView.prototype.events, {
            'click .isic-images-facet-all-exclude': function (event) {
                this.filter.setAllIncluded(false);
            },
            'click .isic-images-facet-all-include': function (event) {
                this.filter.setAllIncluded(true);
            }
        });
    },

    /**
     * @param {ImagesFacetModel} settings.completeFacet
     * @param {ImagesFacetModel} settings.filteredFacet
     * @param {ImagesFilter} settings.filter
     */
    initialize: function (settings) {
        ImagesFacetView.prototype.initialize.call(this, settings);

        this.scale = new HistogramScale();

        // Cached properties from initial render. The initial render is expected
        // to have the full expected space available for the element so that
        // valid values can be cached. Subsequent renders may occur while the
        // element is hidden, which can lead to incorrect size computations when
        // getComputedTextLength() is called.
        this.renderCache = {
            maxBoxHeight: 0,
            // Shortened bin labels
            shortenedLabels: []
        };

        this.listenTo(this.filteredFacet, 'change', this._renderHistogram);
        this.listenTo(this.filter, 'change', this._renderHistogram);
    },

    render: function () {
        this.$el.html(ImagesFacetHistogramTemplate({
            title: this.title,
            facetContentId: this.facetContentId
        }));
        this._renderHistogram();
        this._applyInitialCollapseState();
    },

    _renderHistogram: function () {
        let svg = d3.select(this.el).select('svg.isic-images-facet-histogram-content');
        if (svg.empty()) {
            // Do nothing until render() has been called
            return;
        }

        let parentWidth = this.el.getBoundingClientRect().width;
        let emSize = parseFloat(svg.style('font-size'));
        this.scale.update(
            this.completeFacet.get('bins'),
            this.filteredFacet.get('bins'),
            emSize, parentWidth);

        let width = this.scale.width;
        let topPadding = 0.5 * emSize;
        let height = this.scale.height + topPadding;

        // Draw the y axis
        let yScale = d3.scale.linear()
            .domain([0, this.scale.yMax])
            .range([height, topPadding]);
        let yAxis = d3.svg.axis()
            .scale(yScale)
            .orient('left')
            .ticks(Math.min(4, this.scale.yMax))
            .tickFormat(d3.format('s'));
        let yAxisObj = svg.select('.yAxis')
            .attr('transform', `translate(${this.scale.leftAxisPadding},0)`)
            .call(yAxis);

        // Move the special buttons into place and attach their events
        svg.select('.isic-images-facet-all')
            .attr('transform',
                `translate(${this.scale.leftAxisPadding - 0.5 * emSize},${height + emSize})`);

        // Draw the bin groups
        let bins = svg.select('.bins').selectAll('.bin')
            .data(
                this._zipFacetBins(),
                // TODO: is a key function needed?
                (d) => d.completeBin.label
            );
        let binsEnter = bins.enter().append('g')
            .attr('class', 'bin');
        bins.exit().remove();

        // Move the bins horizontally
        bins.attr('transform', (d) => {
            // TODO: There should be a better way to do this
            let binNo = _.findIndex(
                this.completeFacet.get('bins'),
                {label: d.completeBin.label}
            );
            return `translate(${this.scale.binToPosition(binNo)},${topPadding})`;
        });

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

        let self = this;

        // Update each bar
        let drawBars = () => {
            bins.select('rect.overview')
                .each(function (d) {
                    // this refers to the DOM element
                    d3.select(this)
                        .attr(self.scale.getBinRect(d.completeBin.label, 'overview'));

                    let getTooltipTitle = () => {
                        let completeCount = d.completeBin.count;
                        let filteredCount = d.filteredBin.count;
                        if (filteredCount === completeCount) {
                            return String(filteredCount);
                        } else {
                            return `${filteredCount} (of ${completeCount})`;
                        }
                    };
                    $(this).tooltip({
                        container: 'body',
                        title: getTooltipTitle
                    });
                    // The title function does not get re-bound if a tooltip already exists
                    $(this).data('bs.tooltip').options.title = getTooltipTitle;
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

                    let el = d3.select(this.parentElement)
                        .select('rect.overview')
                        .node();

                    // Delegate "mouseover" events to the tooltip on the
                    // overview bar (so that it appears on top of the bar
                    // itself, not at the top of the bar space).
                    d3.select(this)
                        .attr(self.scale.getFullRect())
                        .on('mouseenter', () => {
                            $(el).tooltip('show');
                        })
                        .on('mouseleave', () => {
                            $(el).tooltip('hide');
                        });
                });
            // Comment out these lines to hide the page histogram (2/2):
            // bins.select('rect.page')
            //     .each(function (d) {
            //         // this refers to the DOM element
            //         d3.select(this).attr(self.scale.getBinRect(d.completeBin.label, 'page'));
            //     });
        };
        drawBars();

        // Add the scale adjustment knob (needs a distinct scale instance)
        let knobScale = yScale.copy();
        let knob = svg.select('.yAxisKnob')
            .attr('transform',
                `translate(${this.scale.leftAxisPadding},${knobScale(this.scale.yMax)})`);
        knob.call(d3.behavior.drag()
            .origin(() => {
                return { x: 0, y: knobScale(this.scale.yMax) };
            }).on('drag', () => {
                // the yMax setter automagically prevents bad values...
                this.scale.yMax = knobScale.invert(d3.event.y);

                // update everything that cares about the y this.scale:
                // the knob
                knob.attr('transform',
                    `translate(${this.scale.leftAxisPadding},${knobScale(this.scale.yMax)})`);
                // the axis
                yScale.domain([0, this.scale.yMax]);
                yAxis.scale(yScale).ticks(Math.min(4, this.scale.yMax));
                yAxisObj.call(yAxis);
                // and the bars
                drawBars();
            }).on('dragstart', () => {
                svg.style('cursor', 'ns-resize');
            }).on('dragend', () => {
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
            .attr('xlink:href', (d) => {
                let status = this.filter.isIncluded(d.completeBin.label);
                if (status === true) {
                    return checkImageUrl;
                } else if (status === false) {
                    return exImageUrl;
                } else {
                    // TODO: this should never happen, until we implement continuous filters
                    // or perhaps if the completeFacetBin.count == 0
                    return dashImageUrl;
                }
            })
            .on('click', (d) => {
                this._toggleBin(d.completeBin.label);
            });

        height += 2 * emSize;

        // Add each bin label, and compute the total needed height
        let offsetY = 0.25 * emSize;
        let transformHeight = height + offsetY;
        let transformAngle = -45;
        let transformAngleRadians = transformAngle * (Math.PI / 180);
        let maxBoxHeight = 0;
        binsEnter.append('text');
        bins.select('text')
            .text((d) => {
                return this._getBinTitle(d.completeBin);
            })
            .attr('text-anchor', 'end')
            .attr('transform', `translate(0 ${transformHeight}) rotate(${transformAngle})`)
            .each(function (d, i) {
                // "this" refers to the DOM element

                // Compute shortened labels and cache for the next render
                let me = d3.select(this);
                let shortenedLabel = self.renderCache.shortenedLabels[i];
                if (!_.isUndefined(shortenedLabel)) {
                    me.html(shortenedLabel);
                } else {
                    // Shorten any labels that are too long. Remove letters from the
                    // end of the string one by one, and replace with an HTML
                    // ellipsis, until the string is a manageable length.
                    let text = me.text();
                    let shortened = false;
                    while (this.getComputedTextLength() > 95) {
                        shortened = true;

                        text = text.slice(0, -1);
                        me.html(`${text}&hellip;`);
                    }

                    self.renderCache.shortenedLabels[i] = me.text();

                    // Add a tooltip to shortened labels, containing the full title.
                    if (shortened) {
                        $(this).tooltip({
                            container: 'body',
                            title: function () {
                                return self._getBinTitle(d.completeBin);
                            }
                        });
                    }
                }

                let boxHeight = Math.abs(this.getComputedTextLength() * Math.sin(transformAngleRadians));
                maxBoxHeight = Math.max(boxHeight, maxBoxHeight);
            });

        // Use maximum box height from current render or cache and update cached value
        maxBoxHeight = Math.max(this.renderCache.maxBoxHeight, maxBoxHeight);
        this.renderCache.maxBoxHeight = maxBoxHeight;

        height += maxBoxHeight + topPadding + offsetY;

        svg.attr({
            width: `${width}px`,
            height: `${height}px`
        });
        return this;
    },

    destroy: function () {
        // Since the tooltips are attached to the HTML <body> (way outside the
        // scope of this view's element, just destroy all tooltip elements
        // globally; this is overkill, but can be fixed in a future refactor
        $('.tooltip').remove();

        ImagesFacetView.prototype.destroy.call(this);
    }
});

const ImagesFacetCategoricalView = ImagesFacetView.extend({
    events: function () {
        return _.extend({}, ImagesFacetView.prototype.events, {
            'click .isic-images-facet-bin': function (event) {
                let binElem = this.$(event.currentTarget);
                let binLabel = binElem.data('binLabel');
                this._toggleBin(binLabel);
            },
            'click .isic-images-facet-all-exclude': function (event) {
                this.filter.setAllIncluded(false);
            },
            'click .isic-images-facet-all-include': function (event) {
                this.filter.setAllIncluded(true);
            }
        });
    },

    /**
     * @param {ImagesFacetModel} settings.completeFacet
     * @param {ImagesFacetModel} settings.filteredFacet
     * @param {ImagesFilter} settings.filterfilters
     */
    initialize: function (settings) {
        ImagesFacetView.prototype.initialize.call(this, settings);

        this.listenTo(this.filteredFacet, 'change', this._rerenderCounts);
        this.listenTo(this.filter, 'change', this._rerenderSelections);
    },

    render: function () {
        this.$el.html(ImagesFacetCategoricalTemplate({
            title: this.title,
            bins: this.completeFacet.get('bins'),
            facetContentId: this.facetContentId,
            getBinTitle: _.bind(this._getBinTitle, this)
        }));

        this._applyInitialCollapseState();
        this._rerenderCounts();
        this._rerenderSelections();
    },

    _rerenderCounts: function () {
        // Both countElems and binVals are guaranteed to be in corresponding order, as they are
        // both created from the same completeBin (and jQuery returns elements in the order on the
        // DOM)
        let countElems = this.$('.isic-images-facet-bin>.isic-images-facet-bin-count');
        let binVals = this._zipFacetBins();
        _.each(_.zip(countElems, binVals), (arg) => {
            let countElem = this.$(arg[0]);
            let binVal = arg[1];

            let completeCount = binVal.completeBin.count;
            let filteredCount = binVal.filteredBin.count;
            let label;
            if (filteredCount === completeCount) {
                label = completeCount;
            } else {
                label = `${filteredCount} / ${completeCount}`;
            }
            label = `(${label})`;

            countElem.text(label);
        });
    },

    _rerenderSelections: function () {
        this.$('.isic-images-facet-bin').each((index, binElem) => {
            let jqBinElem = this.$(binElem);
            let checkElem = jqBinElem.find('i');
            let binLabel = jqBinElem.data('binLabel');
            let binIncluded = this.filter.isIncluded(binLabel);
            checkElem
                .toggleClass('icon-check', binIncluded)
                .toggleClass('icon-check-empty', !binIncluded);
        });
    }
});

const ImagesFacetCategoricalDatasetView = ImagesFacetCategoricalView.extend({
    /**
     * @param {ImagesFacetModel} settings.completeFacet
     * @param {ImagesFacetModel} settings.filteredFacet
     * @param {ImagesFilter} settings.filter
     */
    initialize: function (settings) {
        ImagesFacetCategoricalView.prototype.initialize.call(this, settings);

        this.datasetCollection = new DatasetCollection();
        this.datasetCollection.pageLimit = Number.MAX_SAFE_INTEGER;
        this.datasetCollection
            .once('g:changed', () => {
                this.render();
            })
            .fetch();
    },

    render: function () {
        ImagesFacetCategoricalView.prototype.render.call(this);

        let self = this;

        this.$('.isic-images-facet-bin').popover({
            trigger: 'hover',
            title: function () {
                // Context is the element that the popover is attached to
                let datasetId = $(this).data('binLabel');
                let datasetModel = self.datasetCollection.get(datasetId);
                return datasetModel.name();
            },
            content: function () {
                // Context is the element that the popover is attached to
                let datasetId = $(this).data('binLabel');
                let datasetModel = self.datasetCollection.get(datasetId);

                // Use dataset description if available
                if (datasetModel.has('description')) {
                    return datasetModel.get('description');
                }

                // Fetch dataset details then update content
                self.listenTo(datasetModel, 'g:fetched', () => {
                    let description = datasetModel.get('description');
                    self.$('.popover-content').html(_.escape(description));
                });
                datasetModel.fetch();
                return 'Loading...';
            },
            delay: {
                'show': 100
            }
        });
    },

    _getBinTitle: function (completeBin) {
        let datasetModel = this.datasetCollection.get(completeBin.label);
        return datasetModel ? datasetModel.name() : completeBin.label;
    }
});

const ImagesFacetCategoricalTagsView = ImagesFacetCategoricalView.extend({
    _getBinTitle: function (completeBin) {
        if (completeBin.label === '__null__') {
            return 'untagged';
        } else {
            return completeBin.label;
        }
    }
});

const FACET_SCHEMA = {
    'meta.datasetId': {
        FacetView: ImagesFacetCategoricalDatasetView,
        FacetFilter: CategoricalFacetFilter,
        coerceToType: 'objectid',
        title: 'Dataset',
        collapsed: true
    },
    'meta.clinical.benign_malignant': {
        FacetView: ImagesFacetHistogramView,
        FacetFilter: CategoricalFacetFilter,
        coerceToType: 'string',
        title: 'Benign or Malignant',
        collapsed: true
    },
    'meta.clinical.age_approx': {
        FacetView: ImagesFacetHistogramView,
        FacetFilter: IntervalFacetFilter,
        coerceToType: 'number',
        interpretation: 'ordinal',
        title: 'Approximate Age',
        lowBound: 0,
        highBound: 90,
        numBins: 9,
        collapsed: true
    },
    'meta.clinical.sex': {
        FacetView: ImagesFacetCategoricalView,
        FacetFilter: CategoricalFacetFilter,
        coerceToType: 'string',
        title: 'Sex',
        collapsed: true
    },
    'meta.clinical.diagnosis_confirm_type': {
        FacetView: ImagesFacetCategoricalView,
        FacetFilter: CategoricalFacetFilter,
        coerceToType: 'string',
        title: 'Type of Diagnosis',
        collapsed: true
    },
    'meta.clinical.diagnosis': {
        FacetView: ImagesFacetCategoricalView,
        FacetFilter: CategoricalFacetFilter,
        coerceToType: 'string',
        title: 'Lesion Diagnosis',
        collapsed: true
    },
    'meta.clinical.nevus_type': {
        FacetView: ImagesFacetCategoricalView,
        FacetFilter: CategoricalFacetFilter,
        coerceToType: 'string',
        title: 'Nevus Type',
        collapsed: true
    },
    'meta.clinical.melanocytic': {
        FacetView: ImagesFacetHistogramView,
        FacetFilter: CategoricalFacetFilter,
        coerceToType: 'boolean',
        title: 'Melanocytic',
        collapsed: true
    },
    'meta.clinical.clin_size_long_diam_mm': {
        FacetView: ImagesFacetHistogramView,
        FacetFilter: IntervalFacetFilter,
        coerceToType: 'number',
        interpretation: 'ordinal',
        title: 'Clinical Size - Longest Diameter (mm)',
        lowBound: 0,
        highBound: 110,
        numBins: 11,
        collapsed: true
    },
    'meta.clinical.personal_hx_mm': {
        FacetView: ImagesFacetHistogramView,
        FacetFilter: CategoricalFacetFilter,
        coerceToType: 'boolean',
        title: 'Personal History of Melanoma',
        collapsed: true
    },
    'meta.clinical.family_hx_mm': {
        FacetView: ImagesFacetHistogramView,
        FacetFilter: CategoricalFacetFilter,
        coerceToType: 'boolean',
        title: 'Family History of Melanoma',
        collapsed: true
    },
    'meta.clinical.mel_thick_mm': {
        FacetView: ImagesFacetHistogramView,
        FacetFilter: IntervalFacetFilter,
        coerceToType: 'number',
        interpretation: 'ordinal',
        title: 'Melanoma Thickness (mm)',
        lowBound: 0,
        highBound: 5,
        numBins: 10,
        collapsed: true
    },
    'meta.clinical.mel_class': {
        FacetView: ImagesFacetCategoricalView,
        FacetFilter: CategoricalFacetFilter,
        coerceToType: 'string',
        title: 'Melanoma Class',
        collapsed: true
    },
    'meta.clinical.mel_type': {
        FacetView: ImagesFacetCategoricalView,
        FacetFilter: CategoricalFacetFilter,
        coerceToType: 'string',
        title: 'Melanoma Type',
        collapsed: true
    },
    'meta.clinical.mel_mitotic_index': {
        FacetView: ImagesFacetCategoricalView,
        FacetFilter: CategoricalFacetFilter,
        coerceToType: 'string',
        title: 'Melanoma Mitotic Index',
        collapsed: true
    },
    'meta.clinical.mel_ulcer': {
        FacetView: ImagesFacetHistogramView,
        FacetFilter: CategoricalFacetFilter,
        coerceToType: 'boolean',
        title: 'Melanoma Ulceration',
        collapsed: true
    },
    'meta.clinical.anatom_site_general': {
        FacetView: ImagesFacetCategoricalView,
        FacetFilter: CategoricalFacetFilter,
        coerceToType: 'string',
        title: 'General Anatomic Site',
        collapsed: true
    },
    'meta.acquisition.image_type': {
        FacetView: ImagesFacetCategoricalView,
        FacetFilter: CategoricalFacetFilter,
        coerceToType: 'string',
        title: 'Image Type',
        collapsed: true
    },
    'meta.acquisition.dermoscopic_type': {
        FacetView: ImagesFacetCategoricalView,
        FacetFilter: CategoricalFacetFilter,
        coerceToType: 'string',
        title: 'Dermoscopic Type',
        collapsed: true
    },
    'meta.tags': {
        FacetView: ImagesFacetCategoricalTagsView,
        FacetFilter: TagsCategoricalFacetFilter,
        coerceToType: 'string',
        title: 'Tags',
        collapsed: true
    }
};

export {
    ImagesFacetHistogramView,
    ImagesFacetCategoricalView,
    ImagesFacetCategoricalDatasetView,
    ImagesFacetCategoricalTagsView,
    FACET_SCHEMA
};

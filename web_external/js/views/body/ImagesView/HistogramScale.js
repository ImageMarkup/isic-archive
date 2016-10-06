(function () {
    // This is simply a helper class (not really a model or a view) that
    // abstracts away some of the nuances of the histogram scales (both x and y)
    function HistogramScale(attrName) {
        this.attrName = attrName;

        // The x scale is a funky one - we may (or may not) have an ordinal chunk
        // and a categorical chunk on the same scale. We want to try to use the
        // available horizontal space, but don't let bars get smaller than 1em
        // wide. Ordinal bars will be mashed together, with 0.25 * barSize of padding
        // on either side of the whole set, whereas categorical bars are spaced out
        // with 0.25 padding on both sides for each individual bar. In addition to
        // drawing, we also need to translate interactions to their nearest bar
        // (TODO: support sub-bin dragging in the ordinal section).
        // Consequently, we write our own scale functions instead of using d3.scale
        // (we need to be able to invert ordinal scales, and decide which range we're
        // actually dealing with)

        // The y scale needs to be independently adjustable; we need to keep track
        // of a custom max y, as well as the actual max value of the data
        this.customYmax = null;
    }
    HistogramScale.prototype.update = function (model, emSize, idealWidth) {
        this.leftAxisPadding = 3 * emSize;
        this.height = 6 * emSize;

        this.coerceToType = model.getAttributeType(this.attrName);
        this.overviewHistogram = model.get('overviewHistogram')[this.attrName] || [];
        this.filteredSetHistogram = model.get('filteredSetHistogram')[this.attrName] || [];
        this.pageHistogram = model.get('pageHistogram')[this.attrName] || [];

        this.dividerIndex = undefined;
        this.dividerPosition = undefined;
        this.realYmax = 0;

        this.ordinalBinCount = 0;
        this.categoricalBinCount = 0;
        this.lowBound;
        this.highBound;
        this.categoricalLookup = {};
        this.overviewLabelLookup = {};
        this.filteredLabelLookup = {};
        this.pageLabelLookup = {};

        // First, how many bins are ordinal vs categorical, and what's the
        // overall ordinal range (if there is one)? Where do we encounter
        // the first categorical value? While we're at it, determine the
        // real max vertical count, and construct bin lookup tables for
        // each histogram.
        _.each(this.overviewHistogram, function (bin, index) {
            if (_.has(bin, 'lowBound') && _.has(bin, 'highBound')) {
                this.ordinalBinCount += 1;
                if (this.lowBound === undefined || bin.lowBound < this.lowBound) {
                    this.lowBound = bin.lowBound;
                }
                if (this.highBound === undefined || bin.highBound > this.highBound) {
                    this.highBound = bin.highBound;
                }
            } else {
                if (this.dividerIndex === undefined) {
                    // The server will return all ordinal bins first
                    this.dividerIndex = this.ordinalBinCount;
                }
                this.categoricalBinCount += 1;
                this.categoricalLookup[bin.label] = index;
            }
            this.overviewLabelLookup[bin.label] = index;
            this.realYmax = Math.max(this.realYmax, bin.count);
        }, this);
        _.each(this.filteredSetHistogram, function (bin, index) {
            this.filteredLabelLookup[bin.label] = index;
        }, this);
        _.each(this.pageHistogram, function (bin, index) {
            this.pageLabelLookup[bin.label] = index;
        }, this);

        // If the new data is shorter than the previous custom
        // customYmax, just clear the custom customYmax
        if (this.customYmax !== null && this.customYmax > this.realYmax) {
            this.customYmax = null;
        }

        // Okay, now for the x scale...
        this.width = idealWidth - this.leftAxisPadding;
        this.barSize = Math.max(emSize,
            this.width / (0.5 + this.ordinalBinCount + 1.5 * this.categoricalBinCount));
        this.barSize = Math.min(3 * emSize, this.barSize);
        this.width = this.leftAxisPadding +
        this.barSize * (0.5 + this.ordinalBinCount + 1.5 * this.categoricalBinCount);

        if (this.categoricalBinCount === 0) {
            this.dividerIndex = this.ordinalBinCount;
        }
        this.dividerPosition = this.leftAxisPadding + this.barSize * (0.5 + this.ordinalBinCount);
    };
    HistogramScale.prototype.binToPosition = function (binNo) {
        // Given a bin number, calculate the center of its bar
        if (binNo < this.dividerIndex) {
            // Ordinal bin
            return this.leftAxisPadding + this.barSize * (0.75 + binNo);
        } else {
            // Categorical bin
            return this.dividerPosition + this.barSize * (1.5 * (binNo - this.dividerIndex) + 0.75);
        }
    };
    HistogramScale.prototype.positionToBin = function (position) {
        // Given a screen position, calculate the closest bin number
        if (position < this.dividerPosition) {
            // Ordinal bin
            position -= this.leftAxisPadding + 0.75 * this.barSize;
            return Math.round(position / this.ordinalBinCount);
        } else {
            // Categorical bin
            position -= this.dividerPosition + 0.75 * this.barSize;
            return Math.round(position / (1.5 * this.categoricalBinCount));
        }
    };
    HistogramScale.prototype.labelToBin = function (value, histogram) {
        // Given a bin label and histogram name, get the bin number
        var lookup;
        if (histogram === 'page') {
            lookup = this.pageLabelLookup;
        } else if (histogram === 'filteredSet') {
            lookup = this.filteredLabelLookup;
        } else {  // default: return the overview label index
            lookup = this.overviewLabelLookup;
        }
        if (!(value in lookup)) {
            return undefined;
        } else {
            return lookup[value];
        }
    };
    HistogramScale.prototype.labelToCount = function (value, histogram) {
        // Given a bin label and histogram name, get the bin number
        var lookup;
        if (histogram === 'page') {
            lookup = this.pageLabelLookup;
            histogram = this.pageHistogram;
        } else if (histogram === 'filteredSet') {
            lookup = this.filteredLabelLookup;
            histogram = this.filteredSetHistogram;
        } else {  // default: return the overview count
            lookup = this.overviewLabelLookup;
            histogram = this.overviewHistogram;
        }
        if (!(value in lookup)) {
            return 0;
        } else {
            return histogram[lookup[value]].count;
        }
    };
    HistogramScale.prototype.getBinRect = function (binLabel, histogram) {
        var barHeight = this.y(this.labelToCount(binLabel, histogram));
        return {
            x: -this.barSize / 2,
            y: this.height - barHeight,
            width: this.barSize,
            height: barHeight
        };
    };
    HistogramScale.prototype.y = function (value) {
        return this.height * value / this.yMax;
    };
    Object.defineProperty(HistogramScale.prototype, 'yMax', {
        get: function () {
            return this.customYmax === null ? this.realYmax : this.customYmax;
        },
        set: function (value) {
            this.customYmax = Math.max(1, Math.min(this.realYmax, value));
        }
    });

    isic.views.ImagesViewSubViews = isic.views.ImagesViewSubViews || {};
    isic.views.ImagesViewSubViews.HistogramScale = HistogramScale;
})();

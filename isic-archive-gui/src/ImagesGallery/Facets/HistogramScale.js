import _ from 'underscore';

// This is simply a helper class (not really a model or a view) that
// abstracts away some of the nuances of the histogram scales (both x and y)
function HistogramScale() {
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
HistogramScale.prototype.update = function (overviewHistogram, filteredSetHistogram, emSize, idealWidth) {
    this.overviewHistogram = overviewHistogram || [];
    this.filteredSetHistogram = filteredSetHistogram || [];

    this.leftAxisPadding = 3 * emSize;
    this.height = 6 * emSize;

    this.dividerIndex = undefined;
    this.dividerPosition = undefined;
    this.realYmax = 0;

    this.ordinalBinCount = 0;
    this.categoricalBinCount = 0;
    this.lowBound = null;
    this.highBound = null;
    this.categoricalLookup = {};
    this.overviewLabelLookup = {};

    // First, how many bins are ordinal vs categorical, and what's the
    // overall ordinal range (if there is one)? Where do we encounter
    // the first categorical value? While we're at it, determine the
    // real max vertical count, and construct bin lookup tables for
    // each histogram.
    _.each(this.overviewHistogram, (bin, index) => {
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
        this.realYmax = Math.max(this.realYmax, bin.count);
    });

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
HistogramScale.prototype.getBinRect = function (binLabel, histogram) {
    if (histogram === 'filteredSet') {
        histogram = this.filteredSetHistogram;
    } else { // default: return the overview count
        histogram = this.overviewHistogram;
    }
    let bin = _.findWhere(histogram, {label: binLabel});
    let binCount = bin ? bin.count : 0;

    let barHeight = this.y(binCount);
    let cap = this.y(this.yMax);

    if (barHeight > cap) {
        barHeight = cap;
    }

    return {
        x: -this.barSize / 2,
        y: this.height - barHeight,
        width: this.barSize,
        height: barHeight
    };
};
HistogramScale.prototype.getFullRect = function () {
    let barHeight = this.y(this.yMax);
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

export default HistogramScale;

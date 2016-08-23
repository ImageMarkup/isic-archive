(function() {
    // This is simply a helper class (not really a model or a view) that
    // abstracts away some of the nuances of the histogram scales (both x and y)
    function HistogramScale(attrName) {
        var self = this;
        self.attrName = attrName;

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
        self.customYmax = null;
    }
    HistogramScale.prototype.update = function (model, emSize, idealWidth) {
        var self = this;
        emSize = emSize;
        self.leftAxisPadding = 3 * emSize;
        self.height = 6 * emSize;

        self.coerceToType = model.getAttributeType(self.attrName);
        self.overviewHistogram = model.get('overviewHistogram')[self.attrName] || [];
        self.filteredSetHistogram = model.get('filteredSetHistogram')[self.attrName] || [];
        self.pageHistogram = model.get('pageHistogram')[self.attrName] || [];

        self.dividerIndex = undefined;
        self.dividerPosition = undefined;
        self.realYmax = 0;

        self.ordinalBinCount = 0;
        self.categoricalBinCount = 0;
        self.lowBound;
        self.highBound;
        self.categoricalLookup = {};
        self.overviewLabelLookup = {};
        self.filteredLabelLookup = {};
        self.pageLabelLookup = {};

        // First, how many bins are ordinal vs categorical, and what's the
        // overall ordinal range (if there is one)? Where do we encounter
        // the first categorical value? While we're at it, determine the
        // real max vertical count, and construct bin lookup tables for
        // each histogram.
        self.overviewHistogram.forEach(function (bin, index) {
            if (bin.hasOwnProperty('lowBound') && bin.hasOwnProperty('highBound')) {
                self.ordinalBinCount += 1;
                if (self.lowBound === undefined || bin.lowBound < self.lowBound) {
                    self.lowBound = bin.lowBound;
                }
                if (self.highBound === undefined || bin.highBound > self.highBound) {
                    self.highBound = bin.highBound;
                }
            } else {
                if (self.dividerIndex === undefined) {
                    // The server will return all ordinal bins first
                    self.dividerIndex = self.ordinalBinCount;
                }
                self.categoricalBinCount += 1;
                self.categoricalLookup[bin.label] = index;
            }
            self.overviewLabelLookup[bin.label] = index;
            self.realYmax = Math.max(self.realYmax, bin.count);
        });
        self.filteredSetHistogram.forEach(function (bin, index) {
            self.filteredLabelLookup[bin.label] = index;
        });
        self.pageHistogram.forEach(function (bin, index) {
            self.pageLabelLookup[bin.label] = index;
        });

        // If the new data is shorter than the previous custom
        // customYmax, just clear the custom customYmax
        if (self.customYmax !== null && self.customYmax > self.realYmax) {
            self.customYmax = null;
        }

        // Okay, now for the x scale...
        self.width = idealWidth - self.leftAxisPadding;
        self.barSize = Math.max(emSize,
            self.width / (0.5 + self.ordinalBinCount + 1.5 * self.categoricalBinCount));
        self.barSize = Math.min(3 * emSize, self.barSize);
        self.width = self.leftAxisPadding +
        self.barSize * (0.5 + self.ordinalBinCount + 1.5 * self.categoricalBinCount);

        if (self.categoricalBinCount === 0) {
            self.dividerIndex = self.ordinalBinCount;
        }
        self.dividerPosition = self.leftAxisPadding + self.barSize * (0.5 + self.ordinalBinCount);
    };
    HistogramScale.prototype.binToPosition = function (binNo) {
        var self = this;
        // Given a bin number, calculate the center of its bar
        if (binNo < self.dividerIndex) {
            // Ordinal bin
            return self.leftAxisPadding + self.barSize * (0.75 + binNo);
        } else {
            // Categorical bin
            return self.dividerPosition + self.barSize * (1.5 * (binNo - self.dividerIndex) + 0.75);
        }
    };
    HistogramScale.prototype.positionToBin = function (position) {
        var self = this;
        // Given a screen position, calculate the closest bin number
        if (position < self.dividerPosition) {
            // Ordinal bin
            position -= self.leftAxisPadding + 0.75 * self.barSize;
            return Math.round(position / self.ordinalBinCount);
        } else {
            // Categorical bin
            position -= self.dividerPosition + 0.75 * self.barSize;
            return Math.round(position / (1.5 * self.categoricalBinCount));
        }
    };
    HistogramScale.prototype.labelToBin = function (value, histogram) {
        var self = this;
        // Given a bin label and histogram name, get the bin number
        var lookup;
        if (histogram === 'page') {
            lookup = self.pageLabelLookup;
        } else if (histogram === 'filtered') {
            lookup = self.filteredLabelLookup;
        } else {  // default: return the overview label index
            lookup = self.overviewLabelLookup;
        }
        if (!(value in lookup)) {
            return undefined;
        } else {
            return lookup[value];
        }
    };
    HistogramScale.prototype.labelToCount = function (value, histogram) {
        var self = this;
        // Given a bin label and histogram name, get the bin number
        var lookup;
        if (histogram === 'page') {
            lookup = self.pageLabelLookup;
            histogram = self.pageHistogram;
        } else if (histogram === 'filtered') {
            lookup = self.filteredLabelLookup;
            histogram = self.filteredSetHistogram;
        } else {  // default: return the overview count
            lookup = self.overviewLabelLookup;
            histogram = self.overviewHistogram;
        }
        if (!(value in lookup)) {
            return 0;
        } else {
            return histogram[lookup[value]].count;
        }
    };
    HistogramScale.prototype.getBinRect = function (binLabel, histogram) {
        var self = this;
        var barHeight = self.y(self.labelToCount(binLabel, histogram));
        return {
            x: -self.barSize / 2,
            y: self.height - barHeight,
            width: self.barSize,
            height: barHeight
        };
    };
    HistogramScale.prototype.y = function (value) {
        var self = this;
        return self.height * value / self.yMax;
    };
    Object.defineProperty(HistogramScale.prototype, 'yMax', {
        get: function () {
            var self = this;
            return self.customYmax === null ? self.realYmax : self.customYmax;
        },
        set: function () {
            var self = this;
            self.customYmax = Math.max(1, Math.min(self.realYmax, value));
        }
    });

    isic.views.ImagesViewSubViews = isic.views.ImagesViewSubViews || {};
    isic.views.ImagesViewSubViews.HistogramScale = HistogramScale;
})();

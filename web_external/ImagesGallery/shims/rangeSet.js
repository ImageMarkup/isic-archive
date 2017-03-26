(function () {
    // These functions define operations on lists of ranges,
    // including comparison, union, and intersection. Each range
    // can have a lowBound, a highBound, both, or neither (where
    // a lowBound or highBound is undefined, that range is unbounded).
    // Note that lowBound and highBound do not need to be numbers;
    // an arbitrary comparator may be supplied.

    function defaultComparator(a, b) {
        if (a < b) {
            return -1;
        } else if (a === b) {
            return 0;
        } else {
            return 1;
        }
    }

    function compareHighBounds(a, b, comparator) {
        comparator = comparator || defaultComparator;
        if (!('highBound' in a)) {
            if (!('highBound' in b)) {
                // neither range is high-bounded
                return 0;
            } else {
                // b is high-bounded, but a is not
                return 1;
            }
        } else {
            if (!('highBound' in b)) {
                // a is high-bounded, but b is not
                return -1;
            } else {
                // which high boundary is higher?
                return comparator(a.highBound, b.highBound);
            }
        }
    }

    function compareLowBounds(a, b, comparator) {
        comparator = comparator || defaultComparator;
        if (!('lowBound' in a)) {
            if (!('lowBound' in b)) {
                // neither range is low-bounded
                return 0;
            } else {
                // b is low-bounded, but a is not
                return -1;
            }
        } else {
            if (!('lowBound' in b)) {
                // a is low-bounded, but b is not
                return 1;
            } else {
                // Which low boundary is lower?
                return comparator(a.lowBound, b.lowBound);
            }
        }
    }

    function compareRanges(a, b, comparator) {
        comparator = comparator || defaultComparator;
        // Compare lowBounds first, then highBounds.
        // Where a bound is missing, the range is open-ended
        // (we don't use Infinity because a and b might not
        // be numbers)
        var comp = compareLowBounds(a, b, comparator);
        if (comp === 0) {
            comp = compareHighBounds(a, b, comparator);
        }
        return comp;
    }

    function mostExtremeValue(values, direction, comparator, excludeUnbounded) {
        comparator = comparator || defaultComparator;
        excludeUnbounded = !!excludeUnbounded;
        var result = null;
        for (var i = 0; i < values.length; i += 1) {
            if (values[i] === null) {
                // ignore null
                continue;
            } else if (values[i] === undefined) {
                if (excludeUnbounded) {
                    continue;
                } else {
                    // found an unbounded range; return our proxy for Infinity (undefined)
                    return undefined;
                }
            } else if (result === null) {
                // first regular value encountered
                result = values[i];
            } else {
                var comp = comparator(values[i], result);
                if (direction === '>' && comp > 0) {
                    // encountered a higher value; replace result
                    result = values[i];
                } else if (direction === '<' && comp < 0) {
                    // encountered a lower value; replace result
                    result = values[i];
                }
            }
        }
        return result;
    }

    function copyRangeList(list) {
        var result = [];
        _.each(list, function (range, index) {
            result.push({});
            if ('lowBound' in range) {
                result[index].lowBound = range.lowBound;
            }
            if ('highBound' in range) {
                result[index].highBound = range.highBound;
            }
        });
        return result;
    }

    function cleanRangeList(list, comparator) {
        comparator = comparator || defaultComparator;
        list = copyRangeList(list).sort(function (a, b) {
            return compareRanges(a, b, comparator);
        });

        var i = 0;
        while (i < list.length) {
            var range = list[i];

            // Throw away any invalid ranges
            if ('highBound' in range && 'lowBound' in range &&
            comparator(range.highBound, range.lowBound) < 0) {
                list.splice(i, 1);
                continue;
            }

            // Merge any overlapping ranges
            if (i > 0) {
                var lastRange = list[i - 1];
                if (!('highBound' in lastRange) || !('lowBound' in range) ||
                        comparator(lastRange.highBound, range.lowBound) >= 0) {
                    lastRange.highBound = mostExtremeValue(
                        [lastRange.highBound, range.highBound], '>', comparator);
                    lastRange.lowBound = mostExtremeValue(
                        [lastRange.lowBound, range.lowBound], '<', comparator);
                    // remove spurious undefined values
                    if (lastRange.highBound === undefined) {
                        delete lastRange.highBound;
                    }
                    if (lastRange.lowBound === undefined) {
                        delete lastRange.lowBound;
                    }
                    list.splice(i, 1);
                    continue;
                }
            }

            i += 1;
        }

        return list;
    }

    function rangeIntersection(list1, list2, comparator) {
        comparator = comparator || defaultComparator;
        var result = [];
        list1 = cleanRangeList(list1);
        list2 = cleanRangeList(list2);
        // TODO: there's probably a more efficient way to do this...
        _.each(list1, function (l1) {
            _.each(list2, function (l2) {
                var newRange = {
                    lowBound: mostExtremeValue([l1.lowBound, l2.lowBound], '>', comparator, true),
                    highBound: mostExtremeValue([l1.highBound, l2.highBound], '<', comparator, true)
                };
                if (newRange.lowBound === null) {
                    delete newRange.lowBound;
                }
                if (newRange.highBound === null) {
                    delete newRange.highBound;
                }
                result.push(newRange);
            });
        });

        return cleanRangeList(result);
    }

    isic.shims = isic.shims || {};
    isic.shims.RangeSet = {
        rangeIntersection: rangeIntersection
    };
})();

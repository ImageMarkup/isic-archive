/* globals emit, params, coerceValue, extractValue, findBinLabel:true */

var dataRow = this;
emit('__passedFilters__', {
    histogram: [{
        count: 1,
        label: 'count'
    }]
});
var attrName;
for (attrName in params.binSettings) {
    if (params.binSettings.hasOwnProperty(attrName)) {
        var value = extractValue(attrName, dataRow);
        value = coerceValue(value, params.binSettings[attrName].coerceToType);
        emit(attrName, {
            histogram: [{
                count: 1,
                label: findBinLabel(value,
                    params.binSettings[attrName].coerceToType,
                    params.binSettings[attrName].lowBound,
                    params.binSettings[attrName].highBound,
                    params.binSettings[attrName].specialBins,
                    params.binSettings[attrName].ordinalBins)
            }]
        });
    }
}

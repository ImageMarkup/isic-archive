/*globals d3*/

// Tool that generates SVG filters that can recolor images
// to whatever color we need.
// Usage: CSS styles should do something like this:
// -webkit-filter: url(#recolorImageToFFFFFF)
// filter: url(#recolorImageToFFFFFF)

window.shims = window.shims || {};
window.shims.recolorImageFilters = function (colorList) {
    var svgDefs = d3.select('body').append('svg')
        .attr('id', 'recolorImageFilters')
        .attr('width', '0')
        .attr('height', '0')
        .append('defs');
    // TODO: can svg element be hidden properly, not just made 0x0?

    // Collect all colors in use
    var allColors = {};
    _.each(Object.keys(colorList), function (colorName) {
        var color = colorList[colorName];
        if (!allColors.hasOwnProperty(color)) {
            allColors[color] = [];
        }
        allColors[color].push(colorName);
    });

    var recolorFilters = svgDefs.selectAll('filter.recolor')
        .data(Object.keys(allColors), function (d) {
            return d;
        });
    var recolorFiltersEnter = recolorFilters.enter().append('filter')
        .attr('class', 'recolor')
        .attr('id', function (d) {
            return 'recolorImageTo' + d.slice(1);
        });
    var cmpTransferEnter = recolorFiltersEnter.append('feComponentTransfer')
        .attr('in', 'SourceAlpha')
        .attr('result', 'color');
    cmpTransferEnter.append('feFuncR')
        .attr('type', 'linear')
        .attr('slope', 0)
        .attr('intercept', function (d) {
            var hexvalue = d.slice(1, 3);
            return Math.pow(parseInt(hexvalue, 16) / 255, 2);
        });
    cmpTransferEnter.append('feFuncG')
        .attr('type', 'linear')
        .attr('slope', 0)
        .attr('intercept', function (d) {
            var hexvalue = d.slice(3, 5);
            return Math.pow(parseInt(hexvalue, 16) / 255, 2);
        });
    cmpTransferEnter.append('feFuncB')
        .attr('type', 'linear')
        .attr('slope', 0)
        .attr('intercept', function (d) {
            var hexvalue = d.slice(5, 7);
            return Math.pow(parseInt(hexvalue, 16) / 255, 2);
        });
};

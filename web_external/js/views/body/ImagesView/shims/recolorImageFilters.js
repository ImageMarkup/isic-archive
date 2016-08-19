function recolorImageFilters(colorList) {
  var svgDefs = d3.select('body').append('svg')
    .attr('id', 'recolorImageFilters')
    .append('defs');

  // Collect all colors in use
  var allColors = {};
  Object.keys(colorList).forEach(function(colorName) {
    var color = colorList[colorName];
    if (!allColors.hasOwnProperty(color)) {
      allColors[color] = [];
    }
    allColors[color].push(colorName);
  });

  // Generate SVG filters that can recolor images to whatever
  // color we need. CSS styles simply do something like
  // filter: url(#recolorImageToFFFFFF)
  var recolorFilters = svgDefs.selectAll('filter.recolor')
    .data(Object.keys(allColors), function (d) { return d; });
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
}

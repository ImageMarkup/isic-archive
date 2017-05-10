var fs = require('fs');
var path = require('path');

var pluginPath = path.basename(path.basename(__dirname));
var possibleGirderPaths = [
    path.basename(path.basename(pluginPath)),
    path.join(path.basename(pluginPath), 'girder'),
    process.cwd()
];

/* This requires ES6 */
/*
var configPath = possibleGirderPaths
    .map(function (possibleGirderPath) {
        return path.join(possibleGirderPath, '.eslintrc');
    })
    .find(function (configPath) {
        try {
            fs.accessSync(configPath);
            return true;
        } catch (ignore) {
            return false;
        }
    });
*/


var possibleConfigPaths = possibleGirderPaths
    .map(function (possibleGirderPath) {
        return path.join(possibleGirderPath, '.eslintrc');
    });
var configPath;
for (var i = 0, len = possibleConfigPaths.length; i < len; ++i) {
    try {
        fs.accessSync(possibleConfigPaths[i]);
        configPath = possibleConfigPaths[i];
        break;
    } catch (ignore) {}
}

module.exports = {
    'extends': configPath
};

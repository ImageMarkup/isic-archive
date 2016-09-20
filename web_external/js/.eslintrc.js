var fs = require('fs');
var path = require('path');

var pluginPath = path.basename(path.basename(__dirname));
var possibleGirderPaths = [
    path.basename(path.basename(pluginPath)),
    path.join(path.basename(pluginPath), 'girder'),
    process.cwd()
];

var configPath = possibleGirderPaths
    .map(function (possibleGirderPath) {
        return path.join(possibleGirderPath, '.eslintrc');
    })
    .find(function (configPath) {
        try {
            fs.accessSync(configPath);
            return true;
        } catch (e) {
            return false;
        }
    });

module.exports = {
    'extends': configPath,
    'globals': {
        'isic': true
    }
};

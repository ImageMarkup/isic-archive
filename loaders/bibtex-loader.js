const BibtexParse = require('bibtex-parse-js');

module.exports = function (content) {
    const value = BibtexParse.toJSON(content);
    return `module.exports = ${JSON.stringify(value)}`;
};

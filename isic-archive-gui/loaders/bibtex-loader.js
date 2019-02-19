const _ = require('underscore');
const BibtexParse = require('bibtex-parse-js');
// Use destructuring assignment to import only the "latex2unicode" named export
const { latex2unicode } = require('mathy-unicode-characters');

function unescapeLatexUnicode(str) {
    // Our BibTeX sources (from Google Scholar) use non-standard character escape sequences

    // Match strings like: "{\l}", "{\'a}", "{\'{a}}", "{\'\i}"
    return str.replace(/{(\\.){?(\\??.?)}?}/g, (match, combiningChar, baseChar) => {
        // Recombine the combining and base components into standard LaTeX escapes
        let newEscape = `${combiningChar}{${baseChar}}`;
        if (!baseChar) {
            // If there is no base component, omit empty brackets, but do include a space
            // Specifically, this is required for
            // "\i " -> "LATIN SMALL LETTER DOTLESS I" ("U00131") and
            // "\l " "LATIN SMALL LETTER L WITH STROKE" ("U00142")
            newEscape = `${combiningChar} `;
        }

        // Lookup the corresponding code point from a hardcoded table
        let unicodePoint = latex2unicode[newEscape];
        if (_.isEqual(unicodePoint, ['U003CC', 'U000F3'])) {
            // latex2unicode maps "\'o" to both
            // "GREEK SMALL LETTER OMICRON WITH TONOS" ("U003CC") and
            // "LATIN SMALL LETTER O WITH ACUTE" ("U000F3")
            // so we will always assume it's the latter
            unicodePoint = 'U000F3';
        } else if (!_.isString(unicodePoint)) {
            throw new Error(`Ambiguous character mapping: "${newEscape}"`);
        }

        // Remove the leading "U"
        unicodePoint = unicodePoint.replace(/^U/, '');
        // Map the string to a hex number, then to a Unicode character
        const unicodeChar = String.fromCodePoint(Number.parseInt(unicodePoint, 16));

        return unicodeChar;
    });
}

module.exports = function (content) {
    const publications = BibtexParse.toJSON(content);

    // TODO: Lodash's "transform" would be helpful here
    _.each(publications, (publication) => {
        if (publication.entryTags.author) {
            publication.entryTags.author = unescapeLatexUnicode(publication.entryTags.author);
        }
        if (publication.entryTags.school) {
            publication.entryTags.school = unescapeLatexUnicode(publication.entryTags.school);
        }
        if (publication.entryTags.title) {
            publication.entryTags.title = unescapeLatexUnicode(publication.entryTags.title);
        }
        if (publication.entryTags.booktitle) {
            publication.entryTags.booktitle = unescapeLatexUnicode(publication.entryTags.booktitle);
        }
    });

    return `module.exports = ${JSON.stringify(publications)}`;
};

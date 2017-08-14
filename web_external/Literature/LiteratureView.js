import _ from 'underscore';

import View from '../view';

import publicationsBibtex from './publications.bibtex';
import LiteraturePageTemplate from './literaturePage.pug';
import './literaturePage.styl';

const LiteratureView = View.extend({
    initialize: function (settings) {
        this.publicationsJson = publicationsBibtex;

        // Sort publications by year, in descending order, then by author, in ascending order
        // TODO: This would probably be easier with Lodash's "sortBy"
        this.publicationsJson.sort((a, b) => {
            const aYear = a.entryTags.year || 0;
            const bYear = b.entryTags.year || 0;
            if (aYear < bYear) {
                return 1;
            } else if (aYear > bYear) {
                return -1;
            } else {
                const aAuthor = a.entryTags.author || '';
                const bAuthor = b.entryTags.author || '';
                return aAuthor > bAuthor ? 1 : -1;
            }
        });

        _.each(this.publicationsJson, (publication) => {
            if (publication.entryTags.author) {
                publication.entryTags.author = this._escapeLatex(publication.entryTags.author);
            }
            if (publication.entryTags.school) {
                publication.entryTags.school = this._escapeLatex(publication.entryTags.school);
            }
            if (publication.entryTags.title) {
                publication.entryTags.title = this._escapeLatex(publication.entryTags.title);
            }
        });

        this.render();
    },

    _escapeLatex: function (str) {
        return str
            .replace(/\\&/g, '&amp;')
            .replace(/{\\`([aeiou])}/g, '&$1grave;')
            .replace(/{\\'([aeiouy])}/g, '&$1acute;')
            .replace(/{\\^([aeiou])}/g, '&$1circ;')
            .replace(/{\\~([ano])}/g, '&$1tilde;')
            .replace(/{\\"([aeiouy])}/g, '&$1uml;')
            .replace(/{\\c([c])}/g, '&$1cedil;')
            .replace(/{\\i}/g, '&#x0131;')
            .replace(/{\\l}/g, '&#x0142;');
    },

    render: function () {
        this.$el.html(LiteraturePageTemplate({
            publications: this.publicationsJson
        }));

        return this;
    }
});

export default LiteratureView;

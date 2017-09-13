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

        this.render();
    },

    render: function () {
        this.$el.html(LiteraturePageTemplate({
            publications: this.publicationsJson
        }));

        return this;
    }
});

export default LiteratureView;

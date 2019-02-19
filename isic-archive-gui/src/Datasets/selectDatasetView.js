import View from '../view';

import SelectDatasetPageTemplate from './selectDatasetPage.pug';

// View for a collection of datasets in a select tag. When user selects a
// dataset, a 'changed' event is triggered with the selected dataset as a
// parameter.
const SelectDatasetView = View.extend({
    events: {
        'change #isic-select-dataset-select': 'datasetChanged'
    },

    /**
     * @param {DatasetCollection} settings.collection
     */
    initialize: function (settings) {
        this.listenTo(this.collection, 'reset', this.render);
        this.render();
    },

    datasetChanged: function () {
        const datasetId = this.$('select').val();
        const dataset = this.collection.get(datasetId);
        dataset.fetch()
            .done(() => {
                this.trigger('changed', dataset);
            });
    },

    render: function () {
        // Destroy previous select2
        let select = this.$('#isic-select-dataset-select');
        select.select2('destroy');

        this.$el.html(SelectDatasetPageTemplate({
            models: this.collection.toArray()
        }));

        // Set up select box
        let placeholder = 'Select a dataset...';
        if (!this.collection.isEmpty()) {
            placeholder += ` (${this.collection.length} available)`;
        }
        select = this.$('#isic-select-dataset-select');
        select.select2({
            placeholder: placeholder,
            dropdownParent: this.$el
        });
        select.focus();

        return this;
    }
});

export default SelectDatasetView;

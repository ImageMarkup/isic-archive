girder.views.IsicDatasetsView = girder.View.extend({
    initialize: function () {
        this.collection = new girder.collections.IsicDatasetCollection();
        this.datasetWidgets = [];

        this.collection.on('g:changed', function () {
            console.log('collection changed', this.collection, this.collection.models);
            this.datasetWidgets = _.map(this.collection.models, function (dataset) {
                console.log('create widget from', dataset);
                return new girder.views.IsicDatasetWidget({
                    parentView: this,
                    dataset: dataset
                });
            }, this);

            this.render();
        }, this).fetch();


    },

    render: function () {
        this.$el.html(girder.templates.datasetList({
            datasets: this.collection.models,
            girder: girder
        }));

        console.log('render next', this.datasetWidgets);

        _.each(this.datasetWidgets, function(datasetWidget, datasetNum) {

            var attachTo = this.$('#dataset' + datasetNum);
            console.log('try to attach to', attachTo);

            datasetWidget.setElement(attachTo).render();

            // datasetWidget.setElement(this.$('#dataset' + datasetNum)).render();
        }, this);

        return this;
    }
});


girder.models.IsicDatasetModel = girder.Model.extend({

});

girder.collections.IsicDatasetCollection = girder.Collection.extend({
    resourceName: 'dataset',
    model: girder.models.IsicDatasetModel
    // TODO: make pageLimit unlimited, or add pagination to the view
});




girder.views.IsicDatasetWidget = girder.View.extend({
    initialize: function (settings) {
        this.datasetModel = settings.dataset;

        new girder.views.LoadingAnimation({
            el: this.$el,
            parentView: this
        }).render();

        this.imageCollection = new girder.collections.IsicImageCollection();
        this.imageCollection.on('g:changed', function () {
            this.render();
        }, this).fetch({
            datasetId: this.datasetModel.id,
            limit: 5
        });
    },

    render: function () {
        this.$el.html(girder.templates.isicDatasetWidget({
            dataset: this.datasetModel,
            images: this.imageCollection.models
        }));
        return this;
    }
});


girder.models.IsicImageModel = girder.Model.extend({

});

girder.collections.IsicImageCollection = girder.Collection.extend({
    resourceName: 'image',
    model: girder.models.IsicImageModel
    // TODO: make pageLimit unlimited, or add pagination to the view
});



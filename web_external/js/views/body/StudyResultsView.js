//
// Annotation study results view
//

// Model for a feature
isic.models.FeatureModel = Backbone.Model.extend({
});

// Model for a feature image
isic.models.FeatureImageModel = Backbone.Model.extend({
});

// Model for a global feature result
isic.models.GlobalFeatureResultModel = Backbone.Model.extend({
});

// Collection of feature models
isic.collections.FeatureCollection = Backbone.Collection.extend({
    model: isic.models.FeatureModel,

    // Update collection from an array of features of the form:
    // { 'id': id, 'name': [name1, name2, ...] }
    update: function (features) {
        var models = _.map(features, function (feature) {
            var featureId = feature['id'];
            var featureNames = feature['name'];
            var model = new isic.models.FeatureModel({
                id: featureId,
                name: featureNames.join(', ')
            });
            return model;
        });
        this.reset(models);
    }
});

// Base view for a single model in an option tag
isic.views.StudyResultsOptionView = isic.View.extend({
    tagName: 'option',

    render: function () {
        this.$el.html(this.getName());
        this.$el.attr('value', this.model.id);
        return this;
    },

    getName: function () {
        return this.model.get('name');
    }
});

// Base view for a collection of models in a select tag
isic.views.StudyResultsSelectView = isic.View.extend({
    events: {
        'change': 'modelChanged'
    },

    initialize: function () {
        this.listenTo(this.collection, 'reset', this.addModels);
    },

    modelChanged: function () {
        this.trigger('changed', this.$el.val());
    },

    setEnabled: function (val) {
        if (val) {
            this.$el.removeAttr('disabled');
        } else {
            this.$el.attr('disabled', 'disabled');
        }
    },

    addModel: function (model) {
        var modelView = this.newOptionView({
            model: model,
            parentView: this
        });
        this.modelViews.push(modelView);
        this.$el.append(modelView.render().el);
    },

    addModels: function () {
        _.each(this.modelViews, function (view) {
            view.remove();
            view.destroy(); // necessary to unregister from parent view
        });
        this.modelViews = [];
        this.collection.each(this.addModel, this);

        this.$el[0].selectedIndex = 0;

        this.setEnabled(true);
    }
});

// View for a single study in an option tag
isic.views.StudyResultsStudyView = isic.views.StudyResultsOptionView.extend({
});

// View for a collection of studies in a select tag
isic.views.StudyResultsSelectStudyView = isic.views.StudyResultsSelectView.extend({
    newOptionView: function (params) {
        return new isic.views.StudyResultsStudyView(params);
    }
});

// View for a single image in an option tag
isic.views.StudyResultsImageView = isic.views.StudyResultsOptionView.extend({
});

// View for a collection of images in a select tag
isic.views.StudyResultsSelectImageView = isic.views.StudyResultsSelectView.extend({
    newOptionView: function (params) {
        return new isic.views.StudyResultsImageView(params);
    }
});

// View for a single user in an option tag
isic.views.StudyResultsUserView = isic.views.StudyResultsOptionView.extend({
    getName: function () {
        return this.model.name() + ' (' + this.model.get('login') + ')';
    }
});

// View for a collection of users in a select tag
isic.views.StudyResultsSelectUserView = isic.views.StudyResultsSelectView.extend({
    newOptionView: function (params) {
        return new isic.views.StudyResultsUserView(params);
    }
});

// View for a single feature in an option tag
isic.views.StudyResultsFeatureView = isic.views.StudyResultsOptionView.extend({
});

// View for a collection of features in a select tag
isic.views.StudyResultsSelectFeatureView = isic.views.StudyResultsSelectView.extend({
    newOptionView: function (params) {
        return new isic.views.StudyResultsFeatureView(params);
    }
});

// Collection of global feature result models
isic.collections.GlobalFeatureResultCollection = Backbone.Collection.extend({
    model: isic.models.GlobalFeatureResultModel,

    // Update collection from annotation object and feature list
    update: function (annotations, features) {
        var models = _.map(features, function (feature) {
            var featureId = feature['id'];
            var featureNames = feature['name'];
            var model = new isic.models.GlobalFeatureResultModel({
                id: featureId,
                name: featureNames.join(', ')
            });
            if (annotations) {
                var featureOptions = _.indexBy(feature['options'], 'id');
                var resultId = annotations[featureId];
                var resultName = featureOptions[resultId]['name'];
                model.set('resultId', resultId);
                model.set('resultName', resultName);
            }
            return model;
        });
        this.reset(models);
    }
});

// View for a global feature table row
isic.views.StudyResultsGlobalFeaturesTableRowView = isic.View.extend({
    tagName: 'tr',

    initialize: function (settings) {
        this.listenTo(this.model, 'change', this.render);
    },

    render: function () {
        this.$el.html(isic.templates.studyResultsGlobalFeatureTableRow({
            feature: this.model
        }));

        return this;
    }
});

// View for a global feature table
isic.views.StudyResultsGlobalFeaturesTableView = isic.View.extend({
    tagName: 'tbody',

    initialize: function (settings) {
        this.listenTo(this.collection, 'reset', this.addModels);
    },

    addModel: function (model) {
        var rowView = new isic.views.StudyResultsGlobalFeaturesTableRowView({
            model: model,
            parentView: this
        });
        this.rowViews.push(rowView);
        this.$el.append(rowView.render().el);
    },

    addModels: function () {
        _.each(this.rowViews, function (view) {
            view.remove();
            view.destroy(); // necessary to unregister from parent view
        });
        this.rowViews = [];
        this.collection.each(this.addModel, this);
    }
});

// View for the annotation results of global features in a featureset
isic.views.StudyResultsGlobalFeaturesView = isic.View.extend({
    initialize: function (settings) {
        this.annotation = settings.annotation;
        this.featureset = settings.featureset;

        this.results = new isic.collections.GlobalFeatureResultCollection();
        this.listenTo(this.featureset, 'change', this.render);
        this.listenTo(this.featureset, 'change', this.updateResults);
        this.listenTo(this.annotation, 'change', this.updateResults);

        this.tableView = new isic.views.StudyResultsGlobalFeaturesTableView({
            collection: this.results,
            parentView: this
        });

        this.updateResults();
        this.render();
    },

    render: function () {
        this.$el.html(isic.templates.studyResultsGlobalFeaturesPage({
            title: 'Global Features',
            hasFeatureset: !_.isUndefined(this.featureset.id),
            hasGlobalFeatures: !_.isEmpty(this.featureset.get('image_features')),
            featureset: this.featureset
        }));

        this.tableView.setElement(
            this.$('#isic-study-results-global-features-table-body')).render();

        return this;
    },

    updateResults: function () {
        this.results.update(
            this.annotation.get('annotations'),
            this.featureset.get('image_features')
        );
    }
});

// View for a local feature image defined by an annotation and local feature
isic.views.StudyResultsFeatureImageView = isic.View.extend({
    initialize: function (settings) {
        this.listenTo(this.model, 'change', this.render);
    },

    render: function () {
        var featureId = this.model.get('featureId');
        var annotationId = this.model.get('annotationId');
        var imageUrl = null;
        if (featureId && annotationId) {
            imageUrl = [girder.apiRoot, 'annotation', annotationId, 'image', featureId].join('/');
        }

        this.$el.html(isic.templates.studyResultsFeatureImagePage({
            imageUrl: imageUrl
        }));
    }
});

// View to allow selecting a local feature from a featureset and to display an
// image showing the annotation for the feature
isic.views.StudyResultsLocalFeaturesView = isic.View.extend({
    initialize: function (settings) {
        this.annotation = settings.annotation;
        this.featureset = settings.featureset;
        this.features = new isic.collections.FeatureCollection();

        this.featureImageModel = new isic.models.FeatureImageModel();

        this.listenTo(this.featureset, 'change', this.render);
        this.listenTo(this.featureset, 'change', this.updateFeatureCollection);
        this.listenTo(this.annotation, 'change', this.updateFeatureImageModel);

        this.selectFeatureView = new isic.views.StudyResultsSelectFeatureView({
            collection: this.features,
            parentView: this
        });

        this.imageView = new isic.views.StudyResultsFeatureImageView({
            model: this.featureImageModel,
            parentView: this
        });

        this.listenTo(this.selectFeatureView, 'changed', this.featureChanged);
    },

    featureChanged: function (featureId) {
        this.featureId = featureId;
        this.updateFeatureImageModel();
    },

    updateFeatureImageModel: function () {
        if (!_.has(this, 'featureId') ||
            !_.has(this.annotation, 'id') ||
            _.isUndefined(this.annotation.id)) {
            return;
        }

        this.featureImageModel.set({
            featureId: this.featureId,
            annotationId: this.annotation.id
        });
    },

    render: function () {
        this.$el.html(isic.templates.studyResultsLocalFeaturesPage({
            title: 'Local Features',
            hasFeatureset: !_.isUndefined(this.featureset.id),
            hasLocalFeatures: !_.isEmpty(this.featureset.get('region_features')),
            featureset: this.featureset
        }));

        this.selectFeatureView.setElement(
            this.$('#isic-study-results-select-local-feature-container')).render();
        this.imageView.setElement(
            this.$('#isic-study-results-local-features-image-container')).render();

        return this;
    },

    updateFeatureCollection: function () {
        delete this.featureId;

        this.features.update(this.featureset.get('region_features'));
    }
});

// View for the results of an annotation study
isic.views.StudyResultsView = isic.View.extend({
    initialize: function (settings) {
        this.studies = new isic.collections.StudyCollection();
        this.studies.pageLimit = Number.MAX_SAFE_INTEGER;

        this.images = new isic.collections.ImageCollection();
        this.images.pageLimit = Number.MAX_SAFE_INTEGER;

        this.users = new girder.collections.UserCollection();
        this.users.pageLimit = Number.MAX_SAFE_INTEGER;

        this.featureset = new isic.models.FeaturesetModel();
        this.annotation = new isic.models.AnnotationModel();

        this.selectStudyView = new isic.views.StudyResultsSelectStudyView({
            collection: this.studies,
            parentView: this
        });

        this.selectImageView = new isic.views.StudyResultsSelectImageView({
            collection: this.images,
            parentView: this
        });

        this.selectUserView = new isic.views.StudyResultsSelectUserView({
            collection: this.users,
            parentView: this
        });

        this.globalFeaturesView = new isic.views.StudyResultsGlobalFeaturesView({
            annotation: this.annotation,
            featureset: this.featureset,
            parentView: this
        });

        this.localFeaturesView = new isic.views.StudyResultsLocalFeaturesView({
            annotation: this.annotation,
            featureset: this.featureset,
            parentView: this
        });

        this.studies.fetch();

        this.listenTo(this.selectStudyView, 'changed', this.studyChanged);
        this.listenTo(this.selectImageView, 'changed', this.imageChanged);
        this.listenTo(this.selectUserView, 'changed', this.userChanged);

        this.render();
    },

    studyChanged: function (studyId) {
        this.images.reset();
        this.users.reset();

        delete this.imageId;
        delete this.userId;

        this.selectImageView.setEnabled(false);
        this.selectUserView.setEnabled(false);

        this.annotation.clear();
        this.featureset.clear();

        // Fetch selected study
        this.study = new isic.models.StudyModel({
            _id: studyId
        }).once('g:fetched', function () {
            // Populate images collection
            var imageModels = _.map(this.study.get('images'), function (image) {
                return new isic.models.ImageModel(image);
            });
            this.images.reset(imageModels);

            // Populate users collection
            var userModels = _.map(this.study.get('users'), function (user) {
                return new girder.models.UserModel(user);
            });
            this.users.reset(userModels);

            // Fetch featureset
            var featureset = new isic.models.FeaturesetModel(this.study.get('featureset'));
            featureset.once('g:fetched', function () {
                this.featureset.set(featureset.attributes);
            }, this).fetch();
        }, this).fetch();
    },

    imageChanged: function (imageId) {
        this.imageId = imageId;
        this.annotation.clear();
        this.fetchAnnotation();
    },

    userChanged: function (userId) {
        this.userId = userId;
        this.annotation.clear();
        this.fetchAnnotation();
    },

    fetchAnnotation: function () {
        if (!_.has(this, 'imageId') ||
            !_.has(this, 'userId')) {
            return;
        }

        var annotations = new isic.collections.AnnotationCollection();
        annotations.once('g:changed', function () {
            if (!annotations.isEmpty()) {
                // Fetch annotation detail
                this.annotation.set(annotations.first().attributes).fetch();
            }
        }, this).fetch({
            studyId: this.study.id,
            userId: this.userId,
            imageId: this.imageId
        });
    },

    render: function () {
        this.$el.html(isic.templates.studyResultsPage({
            title: 'Annotation Study Results'
        }));

        this.selectStudyView.setElement(
            this.$('#isic-study-results-select-study-container')).render();
        this.selectImageView.setElement(
            this.$('#isic-study-results-select-image-container')).render();
        this.selectUserView.setElement(
            this.$('#isic-study-results-select-user-container')).render();
        this.globalFeaturesView.setElement(
            this.$('#isic-study-results-global-features-container')).render();
        this.localFeaturesView.setElement(
            this.$('#isic-study-results-local-features-container')).render();

        return this;
    }
});

isic.router.route('studyResults', 'studyResults', function (id) {
    girder.events.trigger('g:navigateTo', isic.views.StudyResultsView);
});

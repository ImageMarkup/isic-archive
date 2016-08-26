//
// Annotation study results view
//

// Model for a feature
isic.models.FeatureModel = Backbone.Model.extend({
    name: function () {
        return this.get('name');
    }
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

// Base view for a collection of models in a select tag
isic.views.StudyResultsSelectView = isic.View.extend({
    events: {
        'change': 'modelChanged'
    },

    initialize: function (options) {
        this.title = options.title;
        this.selectId = _.uniqueId('isic-study-results-select-view-select-');
        this.getName = options.getName || this._defaultGetName;
        this.listenTo(this.collection, 'reset', this.render);

        this.render();
    },

    modelChanged: function () {
        this.trigger('changed', this._element().val());
    },

    setEnabled: function (val) {
        if (val) {
            this._element().removeAttr('disabled');
        } else {
            this._element().attr('disabled', 'disabled');
        }
    },

    update: function () {
        this.render();
        this._element().selectedIndex = 0;
        this.setEnabled(true);
    },

    render: function () {
        this.$el.html(isic.templates.studyResultsSelectView({
            title: this.title,
            selectId: this.selectId,
            getName: this.getName,
            models: this.collection.models
        }));

        return this;
    },

    _element: function () {
        return this.$('select');
    },

    _defaultGetName: function (model) {
        return model.name();
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

// View for a global feature table
isic.views.StudyResultsGlobalFeaturesTableView = isic.View.extend({
    initialize: function (settings) {
        this.listenTo(this.collection, 'reset', this.render);
    },

    render: function () {
        this.$el.html(isic.templates.studyResultsGlobalFeaturesTable({
            features: this.collection.models
        }));
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
            this.$('#isic-study-results-global-features-table')).render();

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
            imageUrl = [
                girder.apiRoot,
                'annotation', annotationId,
                'render?contentDisposition=inline&featureId='
            ].join('/') + encodeURIComponent(featureId);
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

        this.selectFeatureView = new isic.views.StudyResultsSelectView({
            title: 'Feature',
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

// View for an image
isic.views.StudyResultsImageView = isic.View.extend({
    initialize: function (settings) {
        this.listenTo(this.model, 'change', this.render);
    },

    render: function () {
        var imageUrl = this.model.id ? this.model.downloadUrl({contentDisposition: 'inline'}) : null;

        this.$el.html(isic.templates.studyResultsImagePage({
            imageUrl: imageUrl
        }));
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

        this.image = new isic.models.ImageModel();
        this.user = new girder.models.UserModel();
        this.featureset = new isic.models.FeaturesetModel();
        this.annotation = new isic.models.AnnotationModel();

        this.selectStudyView = new isic.views.StudyResultsSelectView({
            title: 'Study',
            collection: this.studies,
            parentView: this
        });

        this.selectImageView = new isic.views.StudyResultsSelectView({
            title: 'Image',
            collection: this.images,
            parentView: this
        });

        this.selectUserView = new isic.views.StudyResultsSelectView({
            title: 'User',
            getName: function (model) {
                return model.get('login');
            },
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

        this.imageView = new isic.views.StudyResultsImageView({
            model: this.image,
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

        this.image.clear();
        this.user.clear();

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
        this.image.set('_id', imageId);
        this.annotation.clear();
        this.fetchAnnotation();
    },

    userChanged: function (userId) {
        this.user.set('_id', userId);
        this.annotation.clear();
        this.fetchAnnotation();
    },

    fetchAnnotation: function () {
        if (!this.image.id ||
            !this.user.id) {
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
            userId: this.user.id,
            imageId: this.image.id
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
        this.imageView.setElement(
            this.$('#isic-study-results-image-container')).render();

        return this;
    }
});

isic.router.route('studyResults', 'studyResults', function (id) {
    girder.events.trigger('g:navigateTo', isic.views.StudyResultsView);
});

import View from '../view';
import ImageModel from '../models/ImageModel';
import SegmentationCollection from '../collections/SegmentationCollection';
import {SegmentationImageViewerWidget} from '../common/Viewer/ImageViewerWidget';

import SegmentationTaskTemplate from './segmentationTask.pug';
import './segmentationTask.styl';

import DetailSegmentationTaskTemplate from './detailSegmentationTask.pug';


const SegmentationTaskView = View.extend({
    initialize: function (settings) {
        this.image = new ImageModel({
            _id: '581cd7319fc3c13dcd0e1ed6'
        });
        this.image
            .once('g:fetched', () => {
                this.segmentations = new SegmentationCollection();
                this.segmentations
                    .once('g:changed', () => {
                        this.segmentation = this.segmentations.at(0);
                        g_segmentation = this.segmentation;

                        this.render();
                    })
                    .fetch({
                        imageId: this.image.id,
                        limit: 0
                    });
            })
            .fetch();

        // if (girder.currentUser.getSegmentationSkill() !== null) {
        //     this.segmentationTasks = new TaskCollection();
        //     this.segmentationTasks.altUrl = 'task/me/segmentation';
        //     this.segmentationTasks.pageLimit = Number.MAX_SAFE_INTEGER;
        //
        //     this.taskSegmentationView = new TasksGroupView({
        //         title: 'Lesion Segmentation',
        //         subtitle: 'Segment boundaries between lesion and normal skin',
        //         linkPrefix: girder.apiRoot + '/task/me/segmentation/redirect?datasetId=',
        //         resourceName: 'dataset',
        //         collection: this.segmentationTasks,
        //         parentView: this
        //     });
        // }
        // this.render();
    },

    render: function () {
        this.$el.html(SegmentationTaskTemplate({
            segmentations: this.segmentations.models,
            formatDate: this.formatDate
        }));

        this.imageViewerWidget = new SegmentationImageViewerWidget({
            el: this.$('.isic-segmentation-task-viewer'),
            model: this.image,
            parentView: this
        }).render();

        this.imageViewerWidget.on('loaded', () => {
            this.imageViewerWidget.addSegmentation(this.segmentation);
        });

        return this;
    }
});

const DetailSegmentationTaskView = View.extend({
    events: {

    },

    initialize: function (settings) {
        this.segmentation = settings.segmentation;

        this.segmentation
            .once('g:fetched', () => {
                this.render();
            })
            .fetch();
    },

    render: function () {
        this.$el.html(DetailSegmentationTaskTemplate({
            segmentation: this.segmentation,
            formatDate: this.formatDate
        }));
        return this;
    }
});

export default SegmentationTaskView;

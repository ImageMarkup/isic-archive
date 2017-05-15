import Collection from './Collection';
import AnnotationModel from '../models/AnnotationModel';

const AnnotationCollection = Collection.extend({
    resourceName: 'annotation',
    model: AnnotationModel
});

export default AnnotationCollection;

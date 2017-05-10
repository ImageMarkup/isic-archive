import Collection from './Collection';
import AnnotationModel from '../models/AnnotationModel';

var AnnotationCollection = Collection.extend({
    resourceName: 'annotation',
    model: AnnotationModel
});

export default AnnotationCollection;

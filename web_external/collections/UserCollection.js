import Collection from './Collection';
import UserModel from '../models/UserModel';

const UserCollection = Collection.extend({
    model: UserModel,

    // ISIC Users may not always contain a 'lastName'
    sortField: 'name',
    secondarySortField: '_id'
});

export default UserCollection;

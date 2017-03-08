isic.collections.UserCollection = girder.collections.UserCollection.extend({
    model: isic.models.UserModel,

    // ISIC Users may not always contain a 'lastName'
    sortField: 'name',
    secondarySortField: '_id'
});

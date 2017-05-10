import Backbone from 'backbone';

import girderRouter from 'girder/router';

// TODO: Why import this just to disable it? Does it get imported somewhere else?
girderRouter.enabled(false);

var router = new Backbone.Router();

export default router;

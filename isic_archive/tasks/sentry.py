import os

import sentry_sdk


sentry_sdk.init(environment=os.getenv('SENTRY_ENVIRONMENT'))

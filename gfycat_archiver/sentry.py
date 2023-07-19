import sentry_sdk
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.httpx import HttpxIntegration

from gfycat_archiver.settings import Settings


def initialise_sentry(settings_: Settings):
    sentry_sdk.init(
        traces_sample_rate=1.0,
        environment=settings_.environment,
        integrations=[
            AsyncioIntegration(),
            HttpxIntegration(),
        ],
    )

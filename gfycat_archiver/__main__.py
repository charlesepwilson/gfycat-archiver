import asyncio
import logging

from gfycat_archiver import archiver, discord_bot, discord_cog, log, sentry, settings

logger = logging.getLogger(__name__)


async def main():
    bot_settings = settings.Settings()  # type: ignore
    sentry.initialise_sentry(bot_settings)
    log.initialise_logger(bot_settings)
    if bot_settings.archive_mode == "local" and bot_settings.save_directory is not None:
        archive = archiver.LocalArchiver(bot_settings.save_directory)
    elif (
        bot_settings.archive_mode == "cloud"
        and bot_settings.cloud_project_id is not None
        and bot_settings.cloud_bucket_name is not None
    ):
        archive = archiver.GoogleCloudArchiver(
            bot_settings.cloud_project_id, bot_settings.cloud_bucket_name
        )
    else:
        raise ValueError("Invalid archive mode")
    bot = await discord_bot.get_bot()
    await discord_cog.setup(
        bot,
        bot_settings.gfycat_client_id,
        bot_settings.gfycat_client_secret,
        archive,
    )
    async with bot:
        await bot.start(bot_settings.discord_token)


if __name__ == "__main__":
    asyncio.run(main())

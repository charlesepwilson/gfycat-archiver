import asyncio
import logging

from gfycat_archiver import discord_bot, discord_cog, log, settings

logger = logging.getLogger(__name__)


async def main():
    bot_settings = settings.Settings()
    log.initialise_logger(bot_settings)
    bot = await discord_bot.get_bot()
    await discord_cog.setup(
        bot,
        bot_settings.gfycat_client_id,
        bot_settings.gfycat_client_secret,
        bot_settings.save_directory,
    )
    async with bot:
        await bot.start(bot_settings.discord_token)


if __name__ == "__main__":
    asyncio.run(main())

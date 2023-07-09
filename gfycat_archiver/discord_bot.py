from discord import Intents
from discord.ext.commands import Bot, when_mentioned

intents_ = Intents(
    guild_messages=True,
    guilds=True,
    messages=True,
    message_content=True,
    members=False,
    auto_moderation=False,
    auto_moderation_configuration=False,
    auto_moderation_execution=False,
    bans=False,
    dm_messages=False,
    dm_reactions=False,
    dm_typing=False,
    emojis=False,
    emojis_and_stickers=False,
    guild_reactions=False,
    guild_scheduled_events=False,
    guild_typing=False,
    integrations=False,
    invites=False,
    presences=False,
    reactions=False,
    typing=False,
    value=False,
    voice_states=False,
    webhooks=False,
)


async def get_bot():
    bot = Bot(command_prefix=when_mentioned, intents=intents_)
    return bot

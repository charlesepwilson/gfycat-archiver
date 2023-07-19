import logging
import re

from discord import Interaction, Message, TextChannel, app_commands
from discord.ext import commands

from gfycat_archiver.archiver import Archiver
from gfycat_archiver.gfycat_download import GfyCatClient, get_gfy_id

logger = logging.getLogger(__name__)


class GfyCatCog(commands.Cog):
    def __init__(
        self,
        bot: commands.Bot,
        client_id: str,
        client_secret: str,
        archiver: Archiver,
    ) -> None:
        self.bot = bot
        self.client_id = client_id
        self.client_secret = client_secret
        self.archiver = archiver
        self.archived_gfycat = app_commands.ContextMenu(
            name="View archived gfycat",
            callback=self.get_file_private,
        )
        self.bot.tree.add_command(self.archived_gfycat)
        self.archived_gfycat_public = app_commands.ContextMenu(
            name="Send archived gfycat",
            callback=self.get_file_public,
        )
        self.bot.tree.add_command(self.archived_gfycat_public)

    @app_commands.command(name="sync")
    @app_commands.describe(
        global_sync="Whether to sync globally or only in this server"
    )
    @app_commands.default_permissions(manage_guild=True)
    async def sync(self, interaction: Interaction, global_sync: bool):
        """Syncs slash commands with discord."""
        if global_sync:
            synced_cmds = await self.bot.tree.sync()
        else:
            # This copies the global commands over to your guild.
            guild = interaction.guild
            if guild is not None:
                self.bot.tree.copy_global_to(guild=guild)
                synced_cmds = await self.bot.tree.sync(guild=guild)

            else:
                await interaction.response.send_message(
                    "Failed to identify guild. This shouldn't ever happen really.",
                    ephemeral=True,
                )
                return
        logger.info(f"{synced_cmds = }")
        await interaction.response.send_message(
            f"Synced commands: {synced_cmds}",
            ephemeral=True,
        )

    @app_commands.command(
        name="archive_channel",
        description="Archives all gfycat links in the current channel",
    )
    async def archive_channel(self, interaction: Interaction):
        # todo record what's already been archived
        # todo archive individual message
        # todo version command
        # todo consider custom plugin for cached_slot_property recognition
        #  https://github.com/kflu/pyprop3/blob/master/pyprop3.iml
        await interaction.response.defer(ephemeral=True, thinking=True)
        assert isinstance(interaction.channel, TextChannel)
        gfycat_links = await get_gfycat_links(interaction.channel)
        with GfyCatClient(self.client_id, self.client_secret, self.archiver) as client:
            client.save_batch(*gfycat_links)
        assert isinstance(interaction.channel, TextChannel)
        await interaction.followup.send(
            f"Successfully archived gfycats in {interaction.channel.name}"
        )

    @app_commands.command(
        name="archive_server",
        description="Archives all gfycat links in the current server",
    )
    async def archive_server(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        with GfyCatClient(self.client_id, self.client_secret, self.archiver) as client:
            assert interaction.guild is not None
            for channel in interaction.guild.text_channels:
                gfycat_links = await get_gfycat_links(channel)
                client.save_batch(*gfycat_links)
        await interaction.followup.send(
            f"Successfully archived gfycats in {interaction.guild.name}"
        )

    async def _get_file(
        self, interaction: Interaction, message: Message, ephemeral: bool = True
    ):
        links = extract_gfycat_links(message.content)
        if not links:
            await interaction.response.send_message(
                "No gfycat link in message", ephemeral=ephemeral
            )
            return
        gfy_id = get_gfy_id(list(links)[0])
        json_file = f"{gfy_id}.json"
        webm_file = f"{gfy_id}.webm"
        json_exists = self.archiver.file_exists(json_file)
        webm_exists = self.archiver.file_exists(webm_file)
        if (not json_exists) or (not webm_exists):
            await interaction.response.send_message(
                "This gfycat has not been archived", ephemeral=ephemeral
            )
            return
        await interaction.response.defer(ephemeral=ephemeral, thinking=True)
        files = self.archiver.attach_files(gfy_id)
        await interaction.followup.send(**files, ephemeral=ephemeral)

    async def get_file_private(self, interaction: Interaction, message: Message):
        return await self._get_file(interaction, message, True)

    async def get_file_public(self, interaction: Interaction, message: Message):
        return await self._get_file(interaction, message, False)


async def setup(
    bot: commands.Bot,
    client_id: str,
    client_secret: str,
    archiver: Archiver,
) -> None:
    await bot.add_cog(GfyCatCog(bot, client_id, client_secret, archiver))


def extract_gfycat_links(text: str) -> set[str]:
    matches = re.findall(r"https://gfycat.com/[a-z]+", text, flags=re.IGNORECASE)
    return set(matches)


async def get_gfycat_links(channel: TextChannel) -> set[str]:
    links = set()
    earliest_time = None
    counter = 1
    while counter:
        counter = 0
        messages = channel.history(before=earliest_time)
        async for message in messages:
            counter += 1
            links.update(extract_gfycat_links(message.content))
            if earliest_time is None or message.created_at < earliest_time:
                earliest_time = message.created_at
    return links

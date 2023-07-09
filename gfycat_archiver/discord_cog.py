import logging
import os
import re
from pathlib import Path

from discord import File, Interaction, Message, TextChannel, app_commands
from discord.ext import commands

from gfycat_archiver.gfycat_download import GfyCatClient, get_gfy_id

logger = logging.getLogger(__name__)


class GfyCatCog(commands.Cog):
    def __init__(
        self,
        bot: commands.Bot,
        client_id: str,
        client_secret: str,
        save_directory: Path,
    ) -> None:
        self.bot = bot
        self.client_id = client_id
        self.client_secret = client_secret
        self.save_directory = save_directory
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

    @commands.command(name="sync")
    async def sync(self, ctx: commands.Context):
        """Syncs slash commands with discord."""
        # This copies the global commands over to your guild.
        guild = ctx.guild
        if guild is not None:
            self.bot.tree.copy_global_to(guild=guild)
            synced_cmds = await self.bot.tree.sync(guild=guild)
            logger.info(f"{synced_cmds = }")
            await ctx.send(f"Synced commands: {synced_cmds}")
        else:
            await ctx.send(
                "Failed to identify guild. This shouldn't ever happen really.",
            )

    @app_commands.command(
        name="archive_channel",
        description="Archives all gfycat links in the current channel",
    )
    async def archive_channel(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        gfycat_links = await get_gfycat_links(interaction.channel)
        with GfyCatClient(
            self.client_id, self.client_secret, self.save_directory
        ) as client:
            client.save_batch(*gfycat_links)
        await interaction.followup.send(
            f"Successfully archived gfycats in {interaction.channel.name}"
        )

    @app_commands.command(
        name="archive_server",
        description="Archives all gfycat links in the current server",
    )
    async def archive_server(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        with GfyCatClient(
            self.client_id, self.client_secret, self.save_directory
        ) as client:
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
        json_exists = os.path.isfile(self.save_directory / json_file)
        webm_exists = os.path.isfile(self.save_directory / webm_file)
        if (not json_exists) or (not webm_exists):
            await interaction.response.send_message(
                "This gfycat has not been archived", ephemeral=ephemeral
            )
            return
        await interaction.response.defer(ephemeral=ephemeral, thinking=True)
        metadata = File(self.save_directory / json_file)
        video = File(self.save_directory / webm_file)
        await interaction.followup.send(files=[metadata, video], ephemeral=ephemeral)

    async def get_file_private(self, interaction: Interaction, message: Message):
        return await self._get_file(interaction, message, True)

    async def get_file_public(self, interaction: Interaction, message: Message):
        return await self._get_file(interaction, message, False)


async def setup(
    bot: commands.Bot,
    client_id: str,
    client_secret: str,
    save_directory: Path,
) -> None:
    await bot.add_cog(GfyCatCog(bot, client_id, client_secret, save_directory))


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

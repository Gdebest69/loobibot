from main import *


class ServerIconCommand(commands.Cog):
    def __init__(self, bot: LoobiBot):
        self.bot = bot

    @app_commands.command(
        name="server-icon",
        description="Get the icon for this server, if it exists",
    )
    @app_commands.guild_only()
    @app_commands.allowed_installs(guilds=True, users=True)
    async def get_server_icon(self, interaction: discord.Interaction):
        # channel check
        if not is_in_guild(interaction):
            await must_use_in_guild(interaction)
            return

        icon = interaction.guild.icon
        if icon is not None:
            await interaction.response.send_message(icon.url, ephemeral=True)
        elif not interaction.is_guild_integration():
            # it is possible to fetch discoverable guilds icons even if the bot is not in it
            try:
                guild_preview = await self.bot.fetch_guild_preview(interaction.guild_id)
                if guild_preview.icon:
                    await interaction.response.send_message(
                        guild_preview.icon.url, ephemeral=True
                    )
                else:
                    await interaction.response.send_message(
                        f"This server has no icon", ephemeral=True
                    )
            except discord.NotFound:
                await interaction.response.send_message(
                    f"This server is not discoverable and I'm not in it", ephemeral=True
                )
        else:
            await interaction.response.send_message(
                f"This server has no icon", ephemeral=True
            )


async def setup(bot: LoobiBot):
    await bot.add_cog(ServerIconCommand(bot))

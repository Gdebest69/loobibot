from main import *


class GroupIconCommand(commands.Cog):
    def __init__(self, bot: LoobiBot):
        self.bot = bot

    @app_commands.command(
        name="group-icon",
        description="Get the icon for this group chat, if it exists",
    )
    @app_commands.user_install()
    @app_commands.allowed_contexts(guilds=False, dms=False, private_channels=True)
    async def group_icon_command(self, interaction: discord.Interaction):
        # channel check
        if not is_in_gc(interaction):
            await interaction.response.send_message(
                "You must use this command inside a group chat",
                ephemeral=True,
            )
            return

        icon = interaction.channel.icon
        if icon is None:
            await interaction.response.send_message(
                f"This group chat has no icon", ephemeral=True
            )
        else:
            await interaction.response.send_message(icon.url, ephemeral=True)


async def setup(bot: LoobiBot):
    await bot.add_cog(GroupIconCommand(bot))

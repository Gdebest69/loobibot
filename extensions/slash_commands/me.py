from main import *


class MeCommand(commands.Cog):
    def __init__(self, bot: LoobiBot):
        self.bot = bot

    @app_commands.command(
        name="me",
        description="Silently mentions you so you can see your roles etc.",
    )
    @app_commands.user_install()
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
    async def get_me_command(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            interaction.user.mention, ephemeral=True
        )


async def setup(bot: LoobiBot):
    await bot.add_cog(MeCommand(bot))

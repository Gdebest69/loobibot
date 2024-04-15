from main import *


class GetAvatarUrlCommand(commands.Cog):
    def __init__(self, bot: LoobiBot):
        self.bot = bot
        self.get_avatar_url_ctx_menu = app_commands.ContextMenu(
            name="Get avatar URL",
            callback=self.get_avatar_url,
        )
        self.bot.tree.add_command(self.get_avatar_url_ctx_menu)

    @app_commands.user_install()
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def get_avatar_url(
        self, interaction: discord.Interaction, user: discord.User
    ):
        message = user.display_avatar.url
        user_avatar = user.avatar if user.avatar is not None else user.default_avatar
        if user_avatar != user.display_avatar:
            message += "\n" + user_avatar.url
        await interaction.response.send_message(message, ephemeral=True)


async def setup(bot: LoobiBot):
    await bot.add_cog(GetAvatarUrlCommand(bot))

from main import *


class GetAvatarUrlCommand(commands.Cog):
    def __init__(self, bot: LoobiBot):
        self.bot = bot
        self.avatar_decoration_to_gif_prefix_url = "https://ezgif.com/apng-to-gif?url="
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
        if user.avatar_decoration is not None:
            convert_avatar_decoration_to_gif_button = discord.ui.Button(
                label="Convert avatar decoration to gif",
                url=self.avatar_decoration_to_gif_prefix_url
                + user.avatar_decoration.url,
            )
            view = discord.ui.View(timeout=None)
            view.add_item(convert_avatar_decoration_to_gif_button)
            message += "\n" + user.avatar_decoration.url
            await interaction.response.send_message(message, view=view, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)


async def setup(bot: LoobiBot):
    await bot.add_cog(GetAvatarUrlCommand(bot))

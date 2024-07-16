from main import *


class GetBannerUrlCommand(commands.Cog):
    def __init__(self, bot: LoobiBot):
        self.bot = bot
        self.get_banner_url_ctx_menu = app_commands.ContextMenu(
            name="Get banner URL",
            callback=self.get_banner_url,
        )
        self.bot.tree.add_command(self.get_banner_url_ctx_menu)

    @app_commands.user_install()
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def get_banner_url(
        self, interaction: discord.Interaction, user: discord.User
    ):
        fetched_user = await self.bot.fetch_user(user.id)
        if isinstance(user, discord.Member) and user.display_banner:
            message = user.display_banner.url
            if fetched_user.banner != user.display_banner:
                message += "\n" + fetched_user.banner.url
            await interaction.response.send_message(message, ephemeral=True)
        elif fetched_user.banner:
            await interaction.response.send_message(
                fetched_user.banner.url, ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "This user doesn't have a custom banner", ephemeral=True
            )


async def setup(bot: LoobiBot):
    await bot.add_cog(GetBannerUrlCommand(bot))

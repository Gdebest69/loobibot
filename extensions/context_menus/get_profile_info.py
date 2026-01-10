from discord import ui
from main import *


class GetProfileInfoCommand(commands.Cog):
    def __init__(self, bot: LoobiBot):
        self.bot = bot
        self.avatar_decoration_to_gif_prefix_url = "https://ezgif.com/apng-to-gif?url="
        self.get_profile_info_ctx_menu = app_commands.ContextMenu(
            name="Get profile info",
            callback=self.get_profile_info,
        )
        self.bot.tree.add_command(self.get_profile_info_ctx_menu)

    @app_commands.user_install()
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def get_profile_info(
        self, interaction: discord.Interaction, user: discord.User
    ):
        global_avatar_url, server_avatar_url = self.get_avatar_urls(user)
        global_banner_url, server_banner_url = await self.get_banner_urls(user)
        nameplate_url = self.get_nameplate_url(user)

        container = ui.Container()
        avatar_gallery = ui.MediaGallery()
        banner_gallery = ui.MediaGallery()
        collectible_gallery = ui.MediaGallery()

        container.add_item(ui.TextDisplay("# Avatar(s)"))
        container.add_item(avatar_gallery)
        if server_avatar_url is None:
            avatar_gallery.add_item(media=global_avatar_url, description="Avatar")
        else:
            avatar_gallery.add_item(
                media=global_avatar_url, description="Global avatar"
            )
            avatar_gallery.add_item(
                media=server_avatar_url, description="Server avatar"
            )
        if user.avatar_decoration is not None:
            avatar_gallery.add_item(
                media=user.avatar_decoration.url, description="Avatar decoration"
            )
            container.add_item(
                ui.ActionRow(
                    ui.Button(
                        label="Convert avatar decoration to gif",
                        url=self.avatar_decoration_to_gif_prefix_url
                        + user.avatar_decoration.url,
                    )
                )
            )

        if global_banner_url is not None:
            banner_name = "Banner" if server_banner_url is None else "Global banner"
            banner_gallery.add_item(media=global_banner_url, description=banner_name)
        if server_banner_url is not None:
            banner_gallery.add_item(
                media=server_banner_url, description="Server banner"
            )
        if banner_gallery.items:
            container.add_item(ui.Separator())
            container.add_item(ui.TextDisplay("# Banner(s)"))
            container.add_item(banner_gallery)

        if nameplate_url is not None:
            collectible_gallery.add_item(media=nameplate_url, description="Nameplate")
        if collectible_gallery.items:
            container.add_item(ui.Separator())
            container.add_item(ui.TextDisplay("# Collectible(s)"))
            container.add_item(collectible_gallery)

        view = ui.LayoutView()
        view.add_item(container)
        await interaction.response.send_message(view=view, ephemeral=True)

    def get_avatar_urls(self, user: discord.User) -> tuple[str, str | None]:
        global_avatar = user.avatar if user.avatar is not None else user.default_avatar
        server_avatar_url = (
            user.display_avatar.url if global_avatar != user.display_avatar else None
        )
        return global_avatar.url, server_avatar_url

    async def get_banner_urls(
        self, user: discord.User
    ) -> tuple[str | None, str | None]:
        fetched_user = await self.bot.fetch_user(user.id)
        global_banner = fetched_user.banner
        server_banner = (
            user.display_banner
            if isinstance(user, discord.Member) and global_banner != user.display_banner
            else None
        )
        return (
            global_banner.url if global_banner is not None else None,
            server_banner.url if server_banner is not None else None,
        )

    def get_nameplate_url(self, user: discord.User) -> str | None:
        for collectible in user.collectibles:
            if collectible.type == discord.CollectibleType.nameplate:
                return collectible.animated.url
        return None


async def setup(bot: LoobiBot):
    await bot.add_cog(GetProfileInfoCommand(bot))

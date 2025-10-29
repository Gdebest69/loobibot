from discord import ui, ButtonStyle
from components.settings_view import SettingsView
from extensions.slash_commands.private_channel import PrivateChannelSettingsView
from extensions.listeners.give_dj_role import DJRolesSettingsView
from extensions.slash_commands.karma import KarmaAmountsSettingsView
from components.commands_usage_view import CommandsUsageSettingsView
from extensions.listeners.auto_channel_status import ActivityStatusSettingsView
from extensions.listeners.auto_roles import AutoRolesSettingsView
from main import *


class ManageSettingsButton(ui.Button[SettingsView]):
    def __init__(self, view_factory):
        super().__init__(label="Manage", style=ButtonStyle.gray)
        self.view_factory = view_factory

    async def callback(self, interaction: discord.Interaction):
        self.view.stop()
        view: SettingsView = self.view_factory()
        await interaction.response.edit_message(view=view)
        view.set_message(self.view.message)


class MainSettingsView(SettingsView):
    def __init__(self, bot: LoobiBot, guild: discord.Guild):
        super().__init__()
        container = ui.Container()
        container.add_item(ui.TextDisplay("# Loobi Bot server settings"))
        container.add_item(
            ui.Separator(visible=False, spacing=discord.SeparatorSpacing.large)
        )
        back_view_factory = lambda: MainSettingsView(bot, guild)
        container.add_item(
            ui.Section(
                "Private channels",
                accessory=ManageSettingsButton(
                    lambda: PrivateChannelSettingsView(bot, guild, back_view_factory)
                ),
            )
        )
        container.add_item(
            ui.Section(
                "DJ roles",
                accessory=ManageSettingsButton(
                    lambda: DJRolesSettingsView(bot, guild, back_view_factory)
                ),
            )
        )
        container.add_item(
            ui.Section(
                "Karma amounts",
                accessory=ManageSettingsButton(
                    lambda: KarmaAmountsSettingsView(bot, guild, back_view_factory)
                ),
            )
        )
        container.add_item(
            ui.Section(
                "Commands usage",
                accessory=ManageSettingsButton(
                    lambda: CommandsUsageSettingsView(bot, guild, back_view_factory)
                ),
            )
        )
        container.add_item(
            ui.Section(
                "Auto channel status",
                accessory=ManageSettingsButton(
                    lambda: ActivityStatusSettingsView(
                        bot.get_guild_data(guild.id).game_status_channels_id,
                        back_view_factory,
                    )
                ),
            )
        )
        container.add_item(
            ui.Section(
                "Auto roles",
                accessory=ManageSettingsButton(
                    lambda: AutoRolesSettingsView(
                        bot.get_guild_data(guild.id), back_view_factory
                    )
                ),
            )
        )
        self.add_item(container)


class SettingsCommand(commands.Cog):
    def __init__(self, bot: LoobiBot):
        self.bot = bot

    @app_commands.command(
        name="settings", description="Change my settings for this guild"
    )
    @app_commands.guild_only()
    @app_commands.allowed_installs(guilds=True, users=False)
    @app_commands.default_permissions()
    async def settings_command(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "You must have administrator permissions to use this command",
                ephemeral=True,
            )
            return

        view = MainSettingsView(self.bot, interaction.guild)
        await interaction.response.send_message(view=view, ephemeral=True)
        view.set_message(await interaction.original_response())


async def setup(bot: LoobiBot):
    await bot.add_cog(SettingsCommand(bot))

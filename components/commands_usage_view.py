from discord import ui
from components.settings_view import SettingsView, ManageChannelsSelect
from main import *


class CommandsSelect(ui.ActionRow["CommandsUsageSettingsView"]):
    def __init__(
        self,
        bot: LoobiBot,
        guild: discord.Guild,
        command_list: list[str],
        placeholder_text: str,
    ):
        super().__init__()
        self.command_list = command_list
        self.select_commands.placeholder = placeholder_text
        for command in bot.tree.get_commands(type=discord.AppCommandType.chat_input):
            if is_guild_installed(command):
                self.select_commands.add_option(label=command.name)
        for command in bot.tree.get_commands(
            guild=guild, type=discord.AppCommandType.chat_input
        ):
            self.select_commands.add_option(label=command.name)
        self.select_commands.max_values = len(self.select_commands.options)
        self.set_default_commands()

    def set_default_commands(self):
        for option in self.select_commands.options:
            option.default = option.label in self.command_list

    @ui.select(min_values=0)
    async def select_commands(
        self, interaction: discord.Interaction, select: ui.Select
    ):
        self.command_list.clear()
        for command_name in select.values:
            self.command_list.append(command_name)
        self.set_default_commands()
        await interaction.response.edit_message(view=self.view)


class CommandsUsageSettingsView(SettingsView):
    def __init__(self, bot: LoobiBot, guild: discord.Guild, back_view_factory):
        super().__init__()
        container = ui.Container()
        container.add_item(ui.TextDisplay("# Commands usage settings"))
        container.add_item(
            ui.Separator(visible=False, spacing=discord.SeparatorSpacing.large)
        )
        container.add_item(ui.TextDisplay("Whitelisted commands"))
        container.add_item(
            CommandsSelect(
                bot,
                guild,
                bot.get_guild_data(guild.id).enabled_commands,
                "Select whitelisted commands",
            )
        )
        container.add_item(ui.TextDisplay("Blacklisted commands"))
        container.add_item(
            CommandsSelect(
                bot,
                guild,
                bot.get_guild_data(guild.id).disabled_commands,
                "Select blacklisted commands",
            )
        )
        container.add_item(ui.Separator())
        channel_types = [
            channel_type
            for channel_type in discord.ChannelType
            if channel_type != discord.ChannelType.category
        ]
        container.add_item(ui.TextDisplay("Whitelisted channels"))
        container.add_item(
            ManageChannelsSelect(
                bot.get_guild_data(guild.id).enabled_channels,
                "Select whitelisted channels",
                channel_types,
            )
        )
        container.add_item(ui.TextDisplay("Blacklisted channels"))
        container.add_item(
            ManageChannelsSelect(
                bot.get_guild_data(guild.id).disabled_channels,
                "Select blacklisted channels",
                channel_types,
            )
        )
        container.add_item(
            ui.TextDisplay("Command restrictions are ignored when admins use them")
        )
        self.add_item(container)
        self.add_back_button(back_view_factory)

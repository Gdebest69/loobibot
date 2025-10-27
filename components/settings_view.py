from discord import ui, ButtonStyle
from main import *


class BackButton(ui.ActionRow["SettingsView"]):
    @ui.button(label="Back", style=ButtonStyle.gray)
    async def go_back(self, interaction: discord.Interaction, button: ui.Button):
        self.view.stop()
        back_view: SettingsView = self.view.back_view_factory()
        await interaction.response.edit_message(view=back_view)
        back_view.set_message(self.view.message)


class SettingsView(ui.LayoutView):
    def __init__(self):
        super().__init__(timeout=TIMEOUT)
        self.message: discord.Message = None
        self.back_view_factory = None

    def add_back_button(self, back_view_factory):
        self.back_view_factory = back_view_factory
        self.add_item(BackButton())

    def set_message(self, message: discord.Message):
        self.message = message

    async def on_timeout(self):
        print(self.__class__.__name__, "timed out")
        if self.message is not None:
            try:
                await self.message.delete()
            except discord.NotFound:
                pass

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.guild_permissions.administrator:
            return True
        await interaction.response.defer()
        return False


class ManageRolesSelect(ui.ActionRow[SettingsView]):
    def __init__(self, role_ids: list[int], placeholder_text: str):
        super().__init__()
        self.role_ids = role_ids
        self.select_roles.placeholder = placeholder_text
        self.set_default_roles()

    def set_default_roles(self):
        self.select_roles.default_values = [
            discord.SelectDefaultValue(
                id=role_id, type=discord.SelectDefaultValueType.role
            )
            for role_id in self.role_ids
        ]

    @ui.select(min_values=0, max_values=MAX_VALUES, cls=ui.RoleSelect)
    async def select_roles(
        self, interaction: discord.Interaction, select: ui.RoleSelect
    ):
        self.role_ids.clear()
        for role in select.values:
            self.role_ids.append(role.id)
        self.set_default_roles()
        await interaction.response.edit_message(view=self.view)


class ManageChannelsSelect(ui.ActionRow[SettingsView]):
    def __init__(
        self,
        channel_ids: list[int],
        placeholder_text: str,
        channel_types: list[discord.ChannelType] = None,
    ):
        super().__init__()
        self.channel_ids = channel_ids
        self.select_channels.placeholder = placeholder_text
        if channel_types is not None:
            self.select_channels.channel_types = channel_types
        self.set_default_channels()

    def set_default_channels(self):
        self.select_channels.default_values = [
            discord.SelectDefaultValue(
                id=channel_id, type=discord.SelectDefaultValueType.channel
            )
            for channel_id in self.channel_ids
        ]

    @ui.select(min_values=0, max_values=MAX_VALUES, cls=ui.ChannelSelect)
    async def select_channels(
        self, interaction: discord.Interaction, select: ui.ChannelSelect
    ):
        self.channel_ids.clear()
        for channel in select.values:
            self.channel_ids.append(channel.id)
        self.set_default_channels()
        await interaction.response.edit_message(view=self.view)

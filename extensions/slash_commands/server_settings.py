from discord.ui import Button, RoleSelect, View, TextInput, Modal, Select, ChannelSelect
from discord import ButtonStyle, TextStyle
from main import *


class ManageRolesView(View):
    def __init__(
        self,
        bot: LoobiBot,
        role_list_name: str,
        role_list_description: str,
        pro_tip: str = None,
    ):
        super().__init__(timeout=TIMEOUT)
        self.role_list_name = role_list_name
        self.role_list_description = role_list_description
        self.pro_tip = pro_tip
        self.message = None
        self.bot = bot

        self.add_roles_select = RoleSelect(
            placeholder="Choose roles to add", max_values=25
        )
        self.add_roles_select.callback = self.add_roles
        self.add_item(self.add_roles_select)

        self.remove_roles_select = RoleSelect(
            placeholder="Choose roles to remove", max_values=25
        )
        self.remove_roles_select.callback = self.remove_roles
        self.add_item(self.remove_roles_select)

    async def send_message(
        self, interaction: discord.Interaction, *, edit: bool = False
    ):
        roles_id = getattr(
            self.bot.get_guild_data(interaction.guild_id), self.role_list_name
        )
        roles = [
            interaction.guild.get_role(role_id)
            for role_id in roles_id
            if interaction.guild.get_role(role_id) is not None
        ]
        sorted_roles = sorted(roles, key=lambda item: item.position)
        setattr(
            self.bot.get_guild_data(interaction.guild_id),
            self.role_list_name,
            [role.id for role in sorted_roles],
        )
        role_list = [role.mention for role in sorted_roles]
        embed = discord.Embed(
            color=EMBED_COLOR,
            title=self.role_list_description,
            description=", ".join(role_list),
        )
        if self.pro_tip is not None:
            embed.set_footer(
                text=self.pro_tip, icon_url=self.bot.user.display_avatar.url
            )
        if edit:
            if self.message is not None:
                await self.message.edit(view=None)
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message(
                embed=embed, view=self, ephemeral=True
            )
            self.message = await interaction.original_response()

    async def add_roles(self, interaction: discord.Interaction):
        roles_id_list: list[int] = getattr(
            self.bot.get_guild_data(interaction.guild_id), self.role_list_name
        )
        for role in self.add_roles_select.values:
            if role.id not in roles_id_list:
                roles_id_list.append(role.id)
        await self.send_message(interaction, edit=True)

    async def remove_roles(self, interaction: discord.Interaction):
        roles_id_list: list[int] = getattr(
            self.bot.get_guild_data(interaction.guild_id), self.role_list_name
        )
        for role in self.remove_roles_select.values:
            if role.id in roles_id_list:
                roles_id_list.remove(role.id)
        await self.send_message(interaction, edit=True)

    async def on_timeout(self):
        if self.message is not None:
            await self.message.edit(view=None)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.defer()
            return False
        return True


class ManageRoleView(View):
    def __init__(self, bot: LoobiBot, role_name: str, role_description: str):
        super().__init__(timeout=TIMEOUT)
        self.role_name = role_name
        self.role_description = role_description
        self.message = None
        self.bot = bot

        self.set_role_select = RoleSelect(placeholder="Choose role")
        self.set_role_select.callback = self.set_role
        self.add_item(self.set_role_select)

        self.clear_button = Button(label="Clear", style=ButtonStyle.red)
        self.clear_button.callback = self.clear_role
        self.add_item(self.clear_button)

    async def send_message(
        self, interaction: discord.Interaction, *, edit: bool = False
    ):
        role_id = getattr(self.bot.get_guild_data(interaction.guild_id), self.role_name)
        role = interaction.guild.get_role(role_id)
        if role is None:
            description = str(None)
        else:
            description = role.mention
        embed = discord.Embed(
            color=EMBED_COLOR, title=self.role_description, description=description
        )
        if edit:
            if self.message is not None:
                await self.message.edit(view=None)
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message(
                embed=embed, view=self, ephemeral=True
            )
            self.message = await interaction.original_response()

    async def set_role(self, interaction: discord.Interaction):
        setattr(
            self.bot.get_guild_data(interaction.guild_id),
            self.role_name,
            self.set_role_select.values[0].id,
        )
        await self.send_message(interaction, edit=True)

    async def clear_role(self, interaction: discord.Interaction):
        setattr(self.bot.get_guild_data(interaction.guild_id), self.role_name, 0)
        await self.send_message(interaction, edit=True)

    async def on_timeout(self):
        if self.message is not None:
            await self.message.edit(view=None)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.defer()
            return False
        return True


class PrivateChannelsCategoryView(View):
    def __init__(self, bot: LoobiBot):
        super().__init__(timeout=TIMEOUT)
        self.message = None
        self.bot = bot

        self.select_category = ChannelSelect(
            placeholder="Choose category",
            channel_types=[discord.ChannelType.category],
        )
        self.select_category.callback = self.set_category
        self.add_item(self.select_category)

        self.clear_button = Button(label="Clear", style=ButtonStyle.red)
        self.clear_button.callback = self.clear_category
        self.add_item(self.clear_button)

    async def send_message(
        self, interaction: discord.Interaction, *, edit: bool = False
    ):
        category_id = self.bot.get_guild_data(
            interaction.guild_id
        ).private_channels_category_id
        category = interaction.guild.get_channel(category_id)
        if category is None:
            description = str(None)
        else:
            description = category.mention
        embed = discord.Embed(
            color=EMBED_COLOR,
            title="Private channels category",
            description=description,
        )
        if edit:
            if self.message is not None:
                await self.message.edit(view=None)
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message(
                embed=embed, view=self, ephemeral=True
            )
            self.message = await interaction.original_response()

    async def set_category(self, interaction: discord.Interaction):
        new_category = self.select_category.values[0]
        self.bot.get_guild_data(interaction.guild_id).private_channels_category_id = (
            new_category.id
        )
        await self.send_message(interaction, edit=True)
        await self.move_channels(interaction, new_category)

    async def clear_category(self, interaction: discord.Interaction):
        self.bot.get_guild_data(interaction.guild_id).private_channels_category_id = 0
        await self.send_message(interaction, edit=True)
        await self.move_channels(interaction, None)

    async def move_channels(
        self, interaction: discord.Interaction, category: discord.CategoryChannel
    ):
        try:
            for channel_id in self.bot.get_guild_data(
                interaction.guild_id
            ).private_channels.values():
                channel = interaction.guild.get_channel(channel_id)
                if channel is not None:
                    await channel.move(
                        category=category,
                        end=True,
                        reason="Moving private channels to new category",
                    )
        except discord.Forbidden:
            pass

    async def on_timeout(self):
        if self.message is not None:
            await self.message.edit(view=None)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.defer()
            return False
        return True


class KarmaAmountsView(View):
    def __init__(self, bot: LoobiBot):
        super().__init__(timeout=TIMEOUT)
        self.message = None
        self.bot = bot

        self.amount_input = TextInput(
            label="Amount", style=TextStyle.short, max_length=5
        )

        self.select_role = RoleSelect(placeholder="Choose role to change")
        self.select_role.callback = self.open_role_menu
        self.add_item(self.select_role)

        self.default_karma_button = Button(
            label="Set default amount", style=ButtonStyle.green
        )
        self.default_karma_button.callback = self.open_default_menu
        self.add_item(self.default_karma_button)

    def default_amount_modal(self):
        default_amount_modal = Modal(title="Choose amount")
        default_amount_modal.add_item(self.amount_input)
        default_amount_modal.on_submit = self.set_default_amount
        return default_amount_modal

    def role_amount_modal(self):
        role_amount_modal = Modal(title="Choose amount")
        role_amount_modal.add_item(self.amount_input)
        role_amount_modal.on_submit = self.set_role_amount
        return role_amount_modal

    async def send_message(
        self, interaction: discord.Interaction, *, edit: bool = False
    ):
        roles_list = []
        amounts_list = []
        for role_id, amount in self.bot.get_guild_data(
            interaction.guild_id
        ).karma_points.items():
            role = interaction.guild.get_role(role_id)
            if role is not None:
                roles_list.append(role.mention)
                amounts_list.append(str(amount))
        roles_str = "\n".join(roles_list)
        amounts_str = "\n".join(amounts_list)
        embed = discord.Embed(
            color=EMBED_COLOR,
            title="Karma amounts",
            description=f"Default karma amount:"
            f" {self.bot.get_guild_data(interaction.guild_id).default_karma_amount}",
        )
        embed.add_field(name="Roles", value=roles_str, inline=True)
        embed.add_field(name="Amount", value=amounts_str, inline=True)
        embed.set_footer(
            text="The lowest roles have higher priority",
            icon_url=self.bot.user.display_avatar.url,
        )
        if edit:
            if self.message is not None:
                await self.message.edit(view=None)
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message(
                embed=embed, view=self, ephemeral=True
            )
            self.message = await interaction.original_response()

    async def open_role_menu(self, interaction: discord.Interaction):
        karma_points = self.bot.get_guild_data(interaction.guild_id).karma_points
        role_id = self.select_role.values[0].id
        if role_id in karma_points:
            self.amount_input.placeholder = str(karma_points[role_id])
        else:
            self.amount_input.placeholder = None
        self.amount_input.label = "Put 0  to clear"
        await interaction.response.send_modal(self.role_amount_modal())

    async def open_default_menu(self, interaction: discord.Interaction):
        self.amount_input.placeholder = str(
            self.bot.get_guild_data(interaction.guild_id).default_karma_amount
        )
        self.amount_input.label = "Default amount"
        await interaction.response.send_modal(self.default_amount_modal())

    async def set_role_amount(self, interaction: discord.Interaction):
        value = self.amount_input.value
        karma_points = self.bot.get_guild_data(interaction.guild_id).karma_points
        role_id = self.select_role.values[0].id
        if value.isdigit():
            value = int(value)
            if value == 0:
                if role_id in karma_points:
                    karma_points.pop(role_id)
            else:
                karma_points[role_id] = value
            self.bot.get_guild_data(interaction.guild_id).karma_points = {
                i[0]: i[1]
                for i in sorted(karma_points.items(), key=lambda item: item[1])
            }
            await self.send_message(interaction, edit=True)
        else:
            await interaction.response.send_message("Invalid value", ephemeral=True)

    async def set_default_amount(self, interaction: discord.Interaction):
        value = self.amount_input.value
        if value.isdigit():
            self.bot.get_guild_data(interaction.guild_id).default_karma_amount = int(
                value
            )
            await self.send_message(interaction, edit=True)
        else:
            await interaction.response.send_message("Invalid value", ephemeral=True)

    async def on_timeout(self):
        if self.message is not None:
            await self.message.edit(view=None)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.defer()
            return False
        return True


class CommandsView(View):
    def __init__(self, bot: LoobiBot):
        super().__init__(timeout=TIMEOUT)
        self.message = None
        self.bot = bot

        self.enable_commands_select = Select(placeholder="Choose commands to enable")
        self.enable_commands_select.callback = self.enable_commands

        self.disable_commands_select = Select(placeholder="Choose commands to disable")
        self.disable_commands_select.callback = self.disable_commands

    async def send_message(
        self, interaction: discord.Interaction, *, edit: bool = False
    ):
        commands = [
            cmd
            for cmd in self.bot.tree.get_commands()
            + self.bot.tree.get_commands(guild=interaction.guild)
            if type(cmd) != app_commands.ContextMenu
        ]
        guild_disabled_commands = self.bot.get_guild_data(
            interaction.guild_id
        ).disabled_commands
        enabled_commands = []
        disabled_commands = []
        self.enable_commands_select.options = []
        self.disable_commands_select.options = []
        for command in commands:
            if command.name in guild_disabled_commands:
                disabled_commands.append(f"`/{command.name}`")
                self.enable_commands_select.add_option(label=command.name)
            else:
                enabled_commands.append(f"`/{command.name}`")
                self.disable_commands_select.add_option(label=command.name)
        embed = discord.Embed(color=EMBED_COLOR, title=f"{self.bot.user.name} commands")
        embed.add_field(
            name="✅ Enabled commands",
            value=", ".join(enabled_commands),
            inline=False,
        )
        embed.add_field(
            name="❌ Disabled commands",
            value=", ".join(disabled_commands),
            inline=False,
        )
        embed.set_footer(
            text="Admins can use disabled commands",
            icon_url=self.bot.user.display_avatar,
        )
        self.remove_item(self.enable_commands_select)
        self.remove_item(self.disable_commands_select)
        if self.enable_commands_select.options:
            if len(self.enable_commands_select.options) > 25:
                self.enable_commands_select.max_values = 25
            else:
                self.enable_commands_select.max_values = len(
                    self.enable_commands_select.options
                )
            self.add_item(self.enable_commands_select)
        if self.disable_commands_select.options:
            if len(self.disable_commands_select.options) > 25:
                self.disable_commands_select.max_values = 25
            else:
                self.disable_commands_select.max_values = len(
                    self.disable_commands_select.options
                )
            self.add_item(self.disable_commands_select)
        if edit:
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message(
                embed=embed, view=self, ephemeral=True
            )
            self.message = await interaction.original_response()

    async def enable_commands(self, interaction: discord.Interaction):
        guild_disabled_commands = self.bot.get_guild_data(
            interaction.guild_id
        ).disabled_commands
        for command in self.enable_commands_select.values:
            if command in guild_disabled_commands:
                guild_disabled_commands.remove(command)
        await self.send_message(interaction, edit=True)

    async def disable_commands(self, interaction: discord.Interaction):
        guild_disabled_commands = self.bot.get_guild_data(
            interaction.guild_id
        ).disabled_commands
        for command in self.disable_commands_select.values:
            if command not in guild_disabled_commands:
                guild_disabled_commands.append(command)
        await self.send_message(interaction, edit=True)

    async def on_timeout(self):
        if self.message is not None:
            await self.message.edit(view=None)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.defer()
            return False
        return True


class ManageDisabledChannelsView(View):
    def __init__(self, bot: LoobiBot):
        super().__init__(timeout=TIMEOUT)
        self.message = None
        self.bot = bot

        all_channel_types = list(discord.ChannelType)
        non_category_channel_types = [
            channel_type
            for channel_type in all_channel_types
            if channel_type != discord.ChannelType.category
        ]

        self.add_channels_select = ChannelSelect(
            placeholder="Choose channels to add to the disabled channels",
            max_values=25,
            channel_types=non_category_channel_types,
        )
        self.add_channels_select.callback = self.add_channels
        self.add_item(self.add_channels_select)

        self.remove_channels_select = ChannelSelect(
            placeholder="Choose channels to remove from the disabled channels",
            max_values=25,
            channel_types=non_category_channel_types,
        )
        self.remove_channels_select.callback = self.remove_channels
        self.add_item(self.remove_channels_select)

        self.add_all_channels_button = Button(
            label="Add all channels", style=ButtonStyle.green
        )
        self.add_all_channels_button.callback = self.add_all_channels
        self.add_item(self.add_all_channels_button)

        self.remove_all_channels_button = Button(label="Clear", style=ButtonStyle.red)
        self.remove_all_channels_button.callback = self.remove_all_channels
        self.add_item(self.remove_all_channels_button)

    async def send_message(
        self, interaction: discord.Interaction, *, edit: bool = False
    ):
        channels_id = self.bot.get_guild_data(interaction.guild_id).disabled_channels
        channels = [
            interaction.guild.get_channel(channel_id)
            for channel_id in channels_id
            if interaction.guild.get_channel(channel_id) is not None
        ]
        sorted_channels = sorted(channels, key=lambda item: item.position)
        self.bot.get_guild_data(interaction.guild_id).disabled_channels = [
            channel.id for channel in sorted_channels
        ]
        channel_list = [channel.mention for channel in sorted_channels]
        embed = discord.Embed(
            color=EMBED_COLOR,
            title="Disabled channels",
            description=", ".join(channel_list),
        )
        embed.set_footer(
            text="Admins can use my commands in disabled channels",
            icon_url=self.bot.user.display_avatar.url,
        )
        if edit:
            if self.message is not None:
                await self.message.edit(view=None)
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message(
                embed=embed, view=self, ephemeral=True
            )
            self.message = await interaction.original_response()

    async def add_channels(self, interaction: discord.Interaction):
        channels_id_list: list[int] = self.bot.get_guild_data(
            interaction.guild_id
        ).disabled_channels
        for channel in self.add_channels_select.values:
            if channel.id not in channels_id_list:
                channels_id_list.append(channel.id)
        await self.send_message(interaction, edit=True)

    async def remove_channels(self, interaction: discord.Interaction):
        channels_id_list: list[int] = self.bot.get_guild_data(
            interaction.guild_id
        ).disabled_channels
        for channel in self.remove_channels_select.values:
            if channel.id in channels_id_list:
                channels_id_list.remove(channel.id)
        await self.send_message(interaction, edit=True)

    async def add_all_channels(self, interaction: discord.Interaction):
        channels_id_list: list[int] = self.bot.get_guild_data(
            interaction.guild_id
        ).disabled_channels
        for channel in interaction.guild.channels:
            if (
                channel.type != discord.ChannelType.category
                and channel.id not in channels_id_list
            ):
                channels_id_list.append(channel.id)
        await self.send_message(interaction, edit=True)

    async def remove_all_channels(self, interaction: discord.Interaction):
        channels_id_list: list[int] = self.bot.get_guild_data(
            interaction.guild_id
        ).disabled_channels
        for channel in interaction.guild.channels:
            if channel.id in channels_id_list:
                channels_id_list.remove(channel.id)
        await self.send_message(interaction, edit=True)

    async def on_timeout(self):
        if self.message is not None:
            await self.message.edit(view=None)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.defer()
            return False
        return True


class GameStatusChannelsView(View):
    def __init__(self, bot: LoobiBot):
        super().__init__(timeout=TIMEOUT)
        self.message = None
        self.bot = bot

        self.add_channels_select = ChannelSelect(
            placeholder="Choose channels to add",
            max_values=25,
            channel_types=[discord.ChannelType.voice],
        )
        self.add_channels_select.callback = self.add_channels
        self.add_item(self.add_channels_select)

        self.remove_channels_select = ChannelSelect(
            placeholder="Choose channels to remove",
            max_values=25,
            channel_types=[discord.ChannelType.voice],
        )
        self.remove_channels_select.callback = self.remove_channels
        self.add_item(self.remove_channels_select)

    async def send_message(
        self, interaction: discord.Interaction, *, edit: bool = False
    ):
        channels_id = self.bot.get_guild_data(
            interaction.guild_id
        ).game_status_channels_id
        channels = [
            interaction.guild.get_channel(channel_id)
            for channel_id in channels_id
            if interaction.guild.get_channel(channel_id) is not None
        ]
        sorted_channels = sorted(channels, key=lambda item: item.position)
        self.bot.get_guild_data(interaction.guild_id).game_status_channels_id = [
            channel.id for channel in sorted_channels
        ]
        channel_list = [channel.mention for channel in sorted_channels]
        embed = discord.Embed(
            color=EMBED_COLOR,
            title="Game status channels",
            description=", ".join(channel_list),
        )
        if edit:
            if self.message is not None:
                await self.message.edit(view=None)
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message(
                embed=embed, view=self, ephemeral=True
            )
            self.message = await interaction.original_response()

    async def add_channels(self, interaction: discord.Interaction):
        channels_id_list = self.bot.get_guild_data(
            interaction.guild_id
        ).game_status_channels_id

        for channel in self.add_channels_select.values:
            if channel.id not in channels_id_list:
                channels_id_list.append(channel.id)
        await self.send_message(interaction, edit=True)

    async def remove_channels(self, interaction: discord.Interaction):
        channels_id_list = self.bot.get_guild_data(
            interaction.guild_id
        ).game_status_channels_id
        for channel in self.remove_channels_select.values:
            if channel.id in channels_id_list:
                channels_id_list.remove(channel.id)
        await self.send_message(interaction, edit=True)

    async def on_timeout(self):
        if self.message is not None:
            await self.message.edit(view=None)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.defer()
            return False
        return True


class AutoRolesFeatureView(View):
    def __init__(self, bot: LoobiBot):
        super().__init__(timeout=TIMEOUT)
        self.message = None
        self.bot = bot

        self.enable_auto_roles_button = Button(
            style=ButtonStyle.green, label="Enable auto roles"
        )
        self.enable_auto_roles_button.callback = self.enable_auto_roles

        self.disable_auto_roles_button = Button(
            style=ButtonStyle.red, label="Disable auto roles"
        )
        self.disable_auto_roles_button.callback = self.disable_auto_roles

    async def send_message(
        self, interaction: discord.Interaction, *, edit: bool = False
    ):
        auto_roles_enabled = self.bot.get_guild_data(
            interaction.guild_id
        ).auto_roles_enabled
        embed = discord.Embed(
            color=EMBED_COLOR,
            title="Auto roles feature",
            description=f"Status: {"**Enabled**" if auto_roles_enabled else "**Disabled**"}",
        )
        if auto_roles_enabled:
            self.add_item(self.disable_auto_roles_button).remove_item(
                self.enable_auto_roles_button
            )
        else:
            self.add_item(self.enable_auto_roles_button).remove_item(
                self.disable_auto_roles_button
            )

        if edit:
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message(
                embed=embed, view=self, ephemeral=True
            )
            self.message = await interaction.original_response()

    async def enable_auto_roles(self, interaction: discord.Interaction):
        self.bot.get_guild_data(interaction.guild_id).auto_roles_enabled = True
        await self.send_message(interaction, edit=True)

    async def disable_auto_roles(self, interaction: discord.Interaction):
        self.bot.get_guild_data(interaction.guild_id).auto_roles_enabled = False
        await self.send_message(interaction, edit=True)

    async def on_timeout(self):
        if self.message is not None:
            await self.message.edit(view=None)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.defer()
            return False
        return True


@app_commands.guild_only()
@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.default_permissions()
class SettingsCommand(
    commands.GroupCog, name="settings", description="Change my settings for this guild"
):
    def __init__(self, bot: LoobiBot):
        self.bot = bot

    async def interaction_check(self, interaction: discord.Interaction):
        # channel check
        if not is_in_guild(interaction):
            await must_use_in_guild(interaction)
            return False

        # permission check
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "You must have administrator permissions to use this command",
                ephemeral=True,
            )
            return False

        return True

    @app_commands.command(
        name="private-channel-roles",
        description="Roles required to create a private channel",
    )
    async def settings_private_channel_roles(self, interaction: discord.Interaction):
        await ManageRolesView(
            self.bot, "private_channel_roles_id", "Private channel roles"
        ).send_message(interaction)

    @app_commands.command(
        name="dj-roles", description="Roles required to get the DJ role"
    )
    async def settings_dj_roles(self, interaction: discord.Interaction):
        await ManageRolesView(
            self.bot,
            "dj_roles_id",
            "DJ roles",
            f"You can change the DJ role using: {self.bot.music.prefix}setdj <rolename|NONE>",
        ).send_message(interaction)

    @app_commands.command(
        name="private-channels-category",
        description="The category where the private channels are",
    )
    async def settings_private_channels_category(
        self, interaction: discord.Interaction
    ):
        await PrivateChannelsCategoryView(self.bot).send_message(interaction)

    @app_commands.command(
        name="karma-amounts",
        description="The amount of karma a user gets when saying gg",
    )
    async def settings_karma_amounts(self, interaction: discord.Interaction):
        await KarmaAmountsView(self.bot).send_message(interaction)

    @app_commands.command(
        name="enabled-commands",
        description="Enabled and disabled commands in this server",
    )
    async def settings_enabled_commands(self, interaction: discord.Interaction):
        await CommandsView(self.bot).send_message(interaction)

    @app_commands.command(
        name="disabled-channels",
        description="Channels that can't be used to run my commands",
    )
    async def settings_disabled_channels(self, interaction: discord.Interaction):
        await ManageDisabledChannelsView(self.bot).send_message(interaction)

    @app_commands.command(
        name="game-status-channels",
        description="Automatically update voice channel status based on members' game activity",
    )
    async def settings_game_status_channels(self, interaction: discord.Interaction):
        await GameStatusChannelsView(self.bot).send_message(interaction)

    @app_commands.command(
        name="auto-roles-feature",
        description="If a member rejoins the server, it will add the roles he had before leaving",
    )
    async def settings_auto_roles_feature(self, interaction: discord.Interaction):
        await AutoRolesFeatureView(self.bot).send_message(interaction)


async def setup(bot: LoobiBot):
    await bot.add_cog(SettingsCommand(bot))

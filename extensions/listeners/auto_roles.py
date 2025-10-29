from discord import ui, ButtonStyle
from components.settings_view import SettingsView, ManageRolesSelect
from main import *


class ToggleAutoRolesButton(ui.ActionRow[SettingsView]):
    def __init__(self, guild_data: GuildData):
        super().__init__()
        self.guild_data = guild_data
        self.update_button()

    def update_button(self):
        self.toggle_auto_roles.label, self.toggle_auto_roles.style = (
            ("Disable auto roles", ButtonStyle.red)
            if self.guild_data.auto_roles_enabled
            else ("Enable auto roles", ButtonStyle.green)
        )

    @ui.button()
    async def toggle_auto_roles(
        self, interaction: discord.Interaction, button: ui.Button
    ):
        self.guild_data.auto_roles_enabled = not self.guild_data.auto_roles_enabled
        self.update_button()
        await interaction.response.edit_message(view=self.view)


class AutoRolesSettingsView(SettingsView):
    def __init__(self, guild_data: GuildData, back_view_factory):
        super().__init__()
        container = ui.Container()
        container.add_item(ui.TextDisplay("# Auto roles settings"))
        container.add_item(
            ui.Separator(visible=False, spacing=discord.SeparatorSpacing.large)
        )
        container.add_item(ui.TextDisplay("Whitelisted roles"))
        container.add_item(
            ManageRolesSelect(guild_data.enabled_auto_roles, "Select whitelisted roles")
        )
        container.add_item(ui.TextDisplay("Blacklisted roles"))
        container.add_item(
            ManageRolesSelect(
                guild_data.disabled_auto_roles, "Select blacklisted roles"
            )
        )
        container.add_item(ui.Separator())
        container.add_item(ToggleAutoRolesButton(guild_data))
        self.add_item(container)
        self.add_back_button(back_view_factory)


class JoinRoles(commands.Cog):
    def __init__(self, bot: LoobiBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        # save roles
        roles_id_list = []
        for role in member.roles:
            roles_id_list.append(role.id)
        roles_id_list.remove(member.guild.default_role.id)
        self.bot.get_guild_data(member.guild.id).roles[member.id] = roles_id_list

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        if not self.bot.get_guild_data(guild.id).auto_roles_enabled:
            return
        # add saved roles
        guild_saved_roles = self.bot.get_guild_data(guild.id).roles
        if member.id in guild_saved_roles:
            added_roles_names = []
            for role_id in guild_saved_roles[member.id]:
                if not is_allowed(
                    role_id,
                    self.bot.get_guild_data(guild.id).enabled_auto_roles,
                    self.bot.get_guild_data(guild.id).disabled_auto_roles,
                ):
                    continue
                role = guild.get_role(role_id)
                if role is not None and role.is_assignable():
                    try:
                        await member.add_roles(role, reason="Auto roles")
                        added_roles_names.append(role.name)
                    except discord.Forbidden:
                        pass
            if added_roles_names:
                self.bot.logger.info(
                    f"Added saved roles for {member} in {member.guild}: {', '.join(added_roles_names)}"
                )


async def setup(bot: LoobiBot):
    await bot.add_cog(JoinRoles(bot))

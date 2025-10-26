from discord import ui, ButtonStyle
from components.settings_view import SettingsView
from components.paged_list_action_row import PagedListActionRow, InvalidPageError
from main import *


class ChangeKarmaAmountButton(ui.Button["KarmaAmountsSettingsView"]):
    def __init__(self, karma_points: dict[int, int], role_id: int):
        super().__init__(label=str(karma_points[role_id]), style=ButtonStyle.blurple)
        self.karma_points = karma_points
        self.role_id = role_id
        self.modal = ui.Modal(title="Change value")
        self.text_input = ui.TextInput(
            default=str(karma_points[role_id]),
            required=False,
            max_length=MAX_KARMA_AMOUNT_LENGTH,
        )
        self.modal.add_item(
            ui.Label(
                text="New value",
                description="Leave empty to clear",
                component=self.text_input,
            )
        )
        self.modal.on_submit = self.on_submit

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(self.modal)

    async def on_submit(self, interaction: discord.Interaction):
        if not self.text_input.value:
            self.view.remove_amount(self.role_id)
            await interaction.response.edit_message(view=self.view)
            return

        if not self.text_input.value.isdigit():
            await interaction.response.send_message(
                "Value must be a positive integer", ephemeral=True
            )
            return

        self.view.apply_amount(self.role_id, int(self.text_input.value))
        try:
            await interaction.response.edit_message(view=self.view)
        except discord.NotFound:
            await interaction.response.defer()


class KarmaAmountsActionRow(PagedListActionRow):
    def __init__(
        self,
        karma_points: dict[int, int],
        guild: discord.Guild,
        settings_view: "KarmaAmountsSettingsView",
    ):
        super().__init__(lambda: self.remove_deleted_roles(), MAX_VALUES_PER_PAGE)
        self.karma_points = karma_points
        self.guild = guild
        self.settings_view = settings_view

    def apply_page(
        self, start_index, stop_index, multiple_pages, page, total_items, total_pages
    ):
        sections = [
            ui.Section(
                self.guild.get_role(role_id).mention,
                accessory=ChangeKarmaAmountButton(self.karma_points, role_id),
            )
            for role_id in list(reversed(self.karma_points.keys()))[
                start_index:stop_index
            ]
        ]
        self.settings_view.build_container(sections, multiple_pages)

    def remove_deleted_roles(self) -> int:
        role_ids_to_pop = [
            role_id
            for role_id in self.karma_points.keys()
            if self.guild.get_role(role_id) is None
        ]
        for role_id in role_ids_to_pop:
            self.karma_points.pop(role_id)
        return len(self.karma_points)

    async def responde_to_interaction(
        self, interaction: discord.Interaction, page_data: None
    ):
        try:
            await interaction.response.edit_message(view=self.settings_view)
        except discord.NotFound:
            await interaction.response.defer()


class AddNewKarmaAmountModal(ui.Modal, title="Add new amount"):
    role_input = ui.Label(
        text="Role", component=ui.RoleSelect(placeholder="Choose a role", required=True)
    )
    value_input = ui.Label(
        text="Value", component=ui.TextInput(max_length=MAX_KARMA_AMOUNT_LENGTH)
    )

    def __init__(self, view: "KarmaAmountsSettingsView"):
        super().__init__()
        self.view = view

    async def on_submit(self, interaction: discord.Interaction):
        assert isinstance(self.role_input.component, ui.RoleSelect)
        assert isinstance(self.value_input.component, ui.TextInput)
        if not self.value_input.component.value.isdigit():
            await interaction.response.send_message(
                "Value must be a positive integer", ephemeral=True
            )
            return

        self.view.apply_amount(
            self.role_input.component.values[0].id,
            int(self.value_input.component.value),
        )
        try:
            await interaction.response.edit_message(view=self.view)
        except discord.NotFound:
            await interaction.response.defer()


class SetDefaultAmountModal(ui.Modal, title="Set default amount"):
    text_input = ui.Label(
        text="Default amount",
        component=ui.TextInput(max_length=MAX_KARMA_AMOUNT_LENGTH),
    )

    def __init__(self, guild_data: GuildData, button: ui.Button):
        super().__init__()
        assert isinstance(self.text_input.component, ui.TextInput)
        self.guild_data = guild_data
        self.button = button
        self.text_input.component.default = str(guild_data.default_karma_amount)

    async def on_submit(self, interaction: discord.Interaction):
        assert isinstance(self.text_input.component, ui.TextInput)
        if not self.text_input.component.value.isdigit():
            await interaction.response.send_message(
                "Value must be a positive integer", ephemeral=True
            )
            return

        self.guild_data.default_karma_amount = int(self.text_input.component.value)
        self.button.label = f"Default amount: {self.guild_data.default_karma_amount}"
        try:
            await interaction.response.edit_message(view=self.button.view)
        except:
            await interaction.response.defer()


class ManageAmountsActionRow(ui.ActionRow["KarmaAmountsSettingsView"]):
    def __init__(self, guild_data: GuildData):
        super().__init__()
        self.guild_data = guild_data
        self.change_default_amount.label = (
            f"Default amount: {guild_data.default_karma_amount}"
        )

    @ui.button(label="+", style=ButtonStyle.blurple)
    async def add_new_karma_amount(
        self, interaction: discord.Interaction, button: ui.Button
    ):
        await interaction.response.send_modal(AddNewKarmaAmountModal(self.view))

    @ui.button(style=ButtonStyle.green)
    async def change_default_amount(
        self, interaction: discord.Interaction, button: ui.Button
    ):
        await interaction.response.send_modal(
            SetDefaultAmountModal(self.guild_data, button)
        )


class KarmaAmountsSettingsView(SettingsView):
    def __init__(self, bot: LoobiBot, guild: discord.Guild, back_view_factory):
        super().__init__()
        self.bot = bot
        self.guild = guild
        self.container = ui.Container()
        self.paged_list_action_row = KarmaAmountsActionRow(
            bot.get_guild_data(guild.id).karma_points, guild, self
        )
        self.paged_list_action_row.update_page()
        self.add_item(self.container)
        self.add_back_button(back_view_factory)

    def build_container(
        self, amounts_sections: list[ui.Section], add_paged_list_action_row: bool
    ):
        self.container.clear_items()
        self.container.add_item(ui.TextDisplay("# Karma amounts settings"))
        self.container.add_item(
            ui.Separator(visible=False, spacing=discord.SeparatorSpacing.large)
        )
        for section in amounts_sections:
            self.container.add_item(section)
        self.container.add_item(
            ManageAmountsActionRow(self.bot.get_guild_data(self.guild.id))
        )
        if add_paged_list_action_row:
            self.container.add_item(self.paged_list_action_row)
        self.container.add_item(ui.TextDisplay("The higher roles have higher priority"))

    def apply_amount(self, role_id: int, amount: int):
        karma_points = self.bot.get_guild_data(self.guild.id).karma_points
        karma_points[role_id] = amount
        sorted_items = sorted(karma_points.items(), key=lambda x: x[1])
        karma_points.clear()
        karma_points.update(sorted_items)
        try:
            self.paged_list_action_row.update_page()
        except InvalidPageError as e:
            self.paged_list_action_row.update_page(e.max_page)

    def remove_amount(self, role_id: int):
        karma_points = self.bot.get_guild_data(self.guild.id).karma_points
        if role_id in karma_points:
            karma_points.pop(role_id)
        try:
            self.paged_list_action_row.update_page()
        except InvalidPageError as e:
            self.paged_list_action_row.update_page(e.max_page)


class KarmaListActionRow(PagedListActionRow):
    def __init__(
        self,
        bot: LoobiBot,
        guild: discord.Guild,
        karma_list_view: "KarmaListView",
        page: int,
    ):
        super().__init__(
            lambda: len(bot.get_guild_data(guild.id).karma),
            MAX_VALUES_PER_PAGE,
            page,
            ButtonStyle.blurple,
        )
        self.bot = bot
        self.guild = guild
        self.karma_list_view = karma_list_view

    def apply_page(
        self, start_index, stop_index, multiple_pages, page, total_items, total_pages
    ) -> discord.Embed:
        member_list = []
        amount_list = []
        karma = sort_dict_by_value(
            self.bot.get_guild_data(self.guild.id).karma, reverse=True
        )
        top_karma = list(karma.items())[start_index:stop_index]
        self.bot.get_guild_data(self.guild.id).karma = karma
        for i, (user_id, amount) in enumerate(top_karma, start_index + 1):
            member_list.append(f"`#{i}` {mention_user(user_id)}")
            amount_list.append(str(amount))
        members_str = "\n".join(member_list)
        amounts_str = "\n".join(amount_list)
        embed = discord.Embed(color=EMBED_COLOR, title="Karma leaderboard")
        embed.add_field(name="Members", value=members_str, inline=True)
        embed.add_field(name="Karma", value=amounts_str, inline=True)
        embed.set_footer(text=f"Page: {page}/{total_pages}")
        return embed

    async def responde_to_interaction(self, interaction, embed):
        await self.karma_list_view.send_message(interaction, embed, edit=True)


class KarmaListView(ui.View):
    def __init__(self, bot: LoobiBot, guild: discord.Guild, page: int):
        super().__init__(timeout=TIMEOUT)
        self.message = None
        self.timed_out = False
        self.action_row = KarmaListActionRow(bot, guild, self, page)
        for button in self.action_row.get_buttons():
            self.add_item(button)

    async def send_message(
        self, interaction: discord.Interaction, embed: discord.Embed, edit: bool = False
    ):
        view = self if not self.timed_out else None
        if edit:
            await interaction.response.edit_message(embed=embed, view=view)
        else:
            await interaction.response.send_message(embed=embed, view=view)
            self.message = await interaction.original_response()

    async def on_timeout(self):
        if self.message is not None:
            try:
                await self.message.edit(view=None)
            except discord.NotFound:
                pass
        self.timed_out = True


@app_commands.guild_only()
@app_commands.allowed_installs(guilds=True, users=False)
class KarmaCommand(
    commands.GroupCog, name="karma", description="Commands related to karma"
):
    def __init__(self, bot: LoobiBot):
        self.bot = bot
        self.get_karma_ctx_menu = app_commands.ContextMenu(
            name="Get karma",
            callback=self.get_karma,
            allowed_installs=app_commands.AppInstallationType(guild=True, user=False),
        )
        self.bot.tree.add_command(self.get_karma_ctx_menu)

    @app_commands.command(
        name="get", description="Check how much karma does a member have"
    )
    @app_commands.describe(member="The member checked")
    async def karma_get(
        self, interaction: discord.Interaction, member: discord.User = None
    ):
        await self.get_karma(interaction, member)

    @app_commands.guild_only()
    async def get_karma(
        self, interaction: discord.Interaction, member: discord.User = None
    ):
        # channel check
        if is_in_dm(interaction):
            await must_use_in_guild(interaction)
            return

        first_person = False
        if member is None:
            member = interaction.user
            first_person = True
        if member.id in self.bot.get_guild_data(interaction.guild_id).karma:
            karma = self.bot.get_guild_data(interaction.guild_id).karma[member.id]
            if first_person:
                await interaction.response.send_message(
                    f"You have {karma} karma", ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    f"{member.mention} has {karma} karma", ephemeral=True
                )
        else:
            if first_person:
                await interaction.response.send_message(
                    "You don't have any karma", ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    f"{member.mention} doesn't have any karma", ephemeral=True
                )

    @app_commands.command(
        name="list", description="A list of the members with the most karma"
    )
    @app_commands.describe(page="The leaderboard page number")
    async def karma_list(self, interaction: discord.Interaction, page: int = 1):
        # channel check
        if is_in_dm(interaction):
            await must_use_in_guild(interaction)
            return

        view = KarmaListView(self.bot, interaction.guild, page)
        await view.send_message(interaction, view.action_row.update_page())

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        # gg
        if plain_message(message.content).lower() == "gg":
            # channel check
            if is_in_dm(message):
                return

            # command check
            if "karma" in self.bot.get_guild_data(message.guild.id).disabled_commands:
                return

            print_message(message, self.bot.logger)
            guild_data = self.bot.get_guild_data(message.guild.id)
            karma_amount = guild_data.default_karma_amount
            for role_id in guild_data.karma_points:
                if has_role(message.author, role_id):
                    karma_amount = guild_data.karma_points[role_id]
            if karma_amount != 0:
                if message.author.id in guild_data.karma:
                    guild_data.karma[message.author.id] += karma_amount
                else:
                    guild_data.karma[message.author.id] = karma_amount
                try:
                    await message.reply(
                        f"+{karma_amount} Karma!",
                        mention_author=False,
                        delete_after=TEMP_MESSAGE_SEC,
                    )
                except discord.Forbidden:
                    pass


async def setup(bot: LoobiBot):
    await bot.add_cog(KarmaCommand(bot))

from discord.ui import View
from discord import ButtonStyle
from components.paged_list_action_row import PagedListActionRow
from main import *


class KarmaListActionRow(PagedListActionRow):
    def __init__(
        self,
        bot: LoobiBot,
        guild: discord.Guild,
        karma_list_view: "KarmaListView",
        page: int,
    ):
        self.bot = bot
        self.guild = guild
        self.karma_list_view = karma_list_view
        super().__init__(
            lambda: len(bot.get_guild_data(guild.id).karma),
            MAX_VALUES_PER_PAGE,
            page,
            ButtonStyle.blurple,
        )

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


class KarmaListView(View):
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
        await view.send_message(interaction, view.action_row.init_page_data)

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

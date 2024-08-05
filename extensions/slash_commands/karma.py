from discord.ui import Button, View
from discord import ButtonStyle
from main import *


class KarmaListView(View):
    def __init__(self, bot: LoobiBot, page: int):
        super().__init__(timeout=TIMEOUT)
        self.message = None
        self.page = page
        self.bot = bot

        self.left_button = Button(emoji="⬅", style=ButtonStyle.blurple)
        self.left_button.callback = self.go_left
        self.add_item(self.left_button)

        self.right_button = Button(emoji="➡", style=ButtonStyle.blurple)
        self.right_button.callback = self.go_right
        self.add_item(self.right_button)

    async def go_left(self, interaction: discord.Interaction):
        self.page -= 1
        await self.send_message(interaction, edit=True)

    async def go_right(self, interaction: discord.Interaction):
        self.page += 1
        await self.send_message(interaction, edit=True)

    async def send_message(self, interaction: discord.Interaction, edit: bool = False):
        # page check
        last_page = (
            len(self.bot.get_guild_data(interaction.guild_id).karma)
            // MAX_VALUES_PER_PAGE
            + 1
        )
        if not 1 <= self.page <= last_page:
            await interaction.response.send_message(
                f"Page number must be between 1 and {last_page}", ephemeral=True
            )
            return

        start_index = (self.page - 1) * MAX_VALUES_PER_PAGE
        end_index = start_index + MAX_VALUES_PER_PAGE
        member_list = []
        amount_list = []
        karma = sort_dict_by_value(
            self.bot.get_guild_data(interaction.guild_id).karma, reverse=True
        )
        top_karma = list(karma.items())[start_index:end_index]
        self.bot.get_guild_data(interaction.guild_id).karma = karma
        for i in range(len(top_karma)):
            member_list.append(
                f"`#{i + start_index + 1}` {mention_user(top_karma[i][0])}"
            )
            amount_list.append(str(top_karma[i][1]))

        if not member_list:
            await interaction.response.send_message(
                "There aren't any members with karma", ephemeral=True
            )
            return

        members_str = "\n".join(member_list)
        amounts_str = "\n".join(amount_list)
        embed = discord.Embed(color=EMBED_COLOR, title="Karma leaderboard")
        embed.add_field(name="Members", value=members_str, inline=True)
        embed.add_field(name="Karma", value=amounts_str, inline=True)
        embed.set_footer(text=f"Page: {self.page}/{last_page}")

        if self.page <= 1:
            self.left_button.disabled = True
        else:
            self.left_button.disabled = False
        if self.page >= last_page:
            self.right_button.disabled = True
        else:
            self.right_button.disabled = False

        if edit:
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message(embed=embed, view=self)
            self.message = await interaction.original_response()

    async def on_timeout(self):
        if self.message is not None:
            try:
                await self.message.edit(view=None)
            except discord.NotFound:
                pass


@app_commands.guild_only()
class KarmaCommand(
    commands.GroupCog, name="karma", description="Commands related to karma"
):
    def __init__(self, bot: LoobiBot):
        self.bot = bot
        self.get_karma_ctx_menu = app_commands.ContextMenu(
            name="Get karma", callback=self.get_karma
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

        await KarmaListView(self.bot, page).send_message(interaction)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        # gg
        if message.content.lower() == "gg":
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

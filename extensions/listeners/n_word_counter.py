from discord.ui import View, Button
from discord import ButtonStyle
from components.paged_list_action_row import PagedListActionRow
from main import *


class NWordListActionRow(PagedListActionRow):
    def __init__(
        self,
        bot: LoobiBot,
        guild: discord.Guild,
        n_word_list_view: "NWordListView",
        page: int,
    ):
        self.bot = bot
        self.guild = guild
        self.n_word_list_view = n_word_list_view
        super().__init__(
            lambda: len(bot.get_guild_data(guild.id).n_words),
            MAX_VALUES_PER_PAGE,
            page,
            ButtonStyle.blurple,
        )

    def apply_page(
        self, start_index, stop_index, multiple_pages, page, total_items, total_pages
    ) -> discord.Embed:
        member_list = []
        amount_list = []
        n_words = sort_dict_by_value(
            self.bot.get_guild_data(self.guild.id).n_words, reverse=True
        )
        top_n_word = list(n_words.items())[start_index:stop_index]
        self.bot.get_guild_data(self.guild.id).n_words = n_words
        for i, (user_id, n_word_count) in enumerate(top_n_word, start_index + 1):
            member_list.append(f"`#{i}` {mention_user(user_id)}")
            amount_list.append(str(n_word_count))
        members_str = "\n".join(member_list)
        amounts_str = "\n".join(amount_list)
        embed = discord.Embed(color=EMBED_COLOR, title="N-word leaderboard")
        embed.add_field(name="Members", value=members_str, inline=True)
        embed.add_field(name="N-word said", value=amounts_str, inline=True)
        embed.set_footer(text=f"Page: {page}/{total_pages}")
        return embed

    async def responde_to_interaction(self, interaction, page_data):
        await self.n_word_list_view.send_message(interaction, page_data, edit=True)


class NWordListView(View):
    def __init__(self, bot: LoobiBot, guild: discord.Guild, page: int):
        super().__init__(timeout=TIMEOUT)
        self.message = None
        self.timed_out = False
        self.action_row = NWordListActionRow(bot, guild, self, page)
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


class NWordCounter(commands.Cog):
    def __init__(self, bot: LoobiBot):
        self.bot = bot
        self.n_words = [
            "nigger",
            "niger",
            "nigga",
            "niga",
            "ניגר",
            "ניגה",
            "כושי",
            "niggers",
            "nigers",
        ]

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # check for n-word
        if is_in_guild(message) and not message.author.bot:
            splitted_content = message.content.split()
            counter = 0
            for n_word in self.n_words:
                for word in splitted_content:
                    if word.lower() == n_word:
                        counter += 1
            if counter > 0:
                n_words = self.bot.get_guild_data(message.guild.id).n_words
                if not message.author.id in n_words:
                    n_words[message.author.id] = 0
                n_words[message.author.id] += counter

    @app_commands.command(
        name="n-leaderboard",
        description="See who said the n-word the most amount of times",
    )
    @app_commands.describe(page="The leaderboard page number")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
    @app_commands.allowed_installs(guilds=True, users=False)
    async def n_leaderboard_command(
        self, interaction: discord.Interaction, page: int = 1
    ):
        # channel check
        if not is_in_guild(interaction):
            await must_use_in_guild(interaction)
            return

        view = NWordListView(self.bot, interaction.guild, page)
        await view.send_message(interaction, view.action_row.init_page_data)


async def setup(bot: LoobiBot):
    await bot.add_cog(NWordCounter(bot))

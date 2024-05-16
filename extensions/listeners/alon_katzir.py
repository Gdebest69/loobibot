from discord.ui import View, Button
from discord import ButtonStyle
from main import *


class NWordListView(View):
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
            len(self.bot.get_guild_data(interaction.guild_id).n_words)
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
        top_n_word = sorted(
            self.bot.get_guild_data(interaction.guild_id).n_words.items(),
            reverse=True,
            key=lambda item: item[1],
        )[start_index:end_index]
        for i in range(len(top_n_word)):
            member_list.append(
                f"`#{i + start_index + 1}` {mention_user(top_n_word[i][0])}"
            )
            amount_list.append(str(top_n_word[i][1]))

        if not member_list:
            await interaction.response.send_message(
                "There aren't any members who said the n-word", ephemeral=True
            )
            return

        members_str = "\n".join(member_list)
        amounts_str = "\n".join(amount_list)
        embed = discord.Embed(color=EMBED_COLOR, title="N-word leaderboard")
        embed.add_field(name="Members", value=members_str, inline=True)
        embed.add_field(name="N-word said", value=amounts_str, inline=True)
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
            await self.message.edit(view=None)


class WeDoSomeLols(commands.Cog):
    def __init__(self, bot: LoobiBot):
        self.bot = bot
        self.reach_id = 294452820353089536
        self.n_words = [
            "nigger",
            "niger",
            "nigga",
            "niga",
            "ניגר",
            "ניגה",
            "niggers",
            "nigers",
        ]

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if (
            message.guild is not None
            and message.guild.id == GUILD_ID
            and "pokemonshowdown.com" in message.content
            and message.author.id == self.reach_id
        ):
            await message.delete()

        # check for n-word
        if is_in_guild(message) and not message.author.bot:
            content = message.content
            for n_word in self.n_words:
                if (
                    content.startswith(n_word)
                    or content.endswith(n_word)
                    or f" {n_word} " in content
                ):
                    n_words = self.bot.get_guild_data(message.guild.id).n_words
                    if not message.author.id in n_words:
                        n_words[message.author.id] = 0
                    n_words[message.author.id] += 1

    @app_commands.command(
        name="n-leaderboard",
        description="See who said the n-word the most amount of times",
    )
    async def n_leaderboard_command(
        self, interaction: discord.Interaction, page: int = 1
    ):
        # channel check
        if not is_in_guild(interaction):
            await must_use_in_guild(interaction)
            return

        await NWordListView(self.bot, page).send_message(interaction)


async def setup(bot: LoobiBot):
    await bot.add_cog(WeDoSomeLols(bot))

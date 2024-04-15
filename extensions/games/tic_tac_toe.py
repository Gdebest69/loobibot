from main import *
from discord.ui import View, Button
from discord import ButtonStyle

X_EMOJI = "❌"
O_EMOJI = "⭕"
EMPTY = "\u200e"


class TicTacToeButton(Button):
    def __init__(self, x: int, y: int):
        super().__init__(style=ButtonStyle.blurple, label=EMPTY, row=y)
        self.x = x
        self.y = y

    def get_shape(self):
        return self.label if self.emoji is None else self.emoji

    async def callback(self, interaction: discord.Interaction):
        view: TicTacToeView = self.view
        if view.current_player.user is None:
            if self.emoji is not None:
                await interaction.response.send_message("Invalid move", ephemeral=True)
                return
            view.player2.user = interaction.user

        if (
            interaction.user != view.player1.user
            and interaction.user != view.player2.user
        ):
            await interaction.response.send_message(
                "You don't play this game", ephemeral=True
            )
            return

        if interaction.user == view.current_player.user:
            if self.emoji is not None:
                await interaction.response.send_message("Invalid move", ephemeral=True)
                return

            self.emoji = view.current_player.shape
            self.label = None
            view.grid[self.y][self.x] = view.current_player.shape
            player = view.current_player
            view.current_player = (
                view.player2 if view.current_player == view.player1 else view.player1
            )
            view.moves += 1
            if view.moves == 2:
                view.remove_item(view.cancel_button)
            await view.update_game(interaction, player)

        else:
            await interaction.response.send_message(
                "This is not your turn", ephemeral=True
            )


class Player:
    def __init__(self, user: discord.User, shape: str):
        self.user = user
        self.shape = shape

    def __str__(self) -> str:
        s = self.user.mention if self.user is not None else "Anyone who wants to play"
        s += f" ({self.shape})"
        return s


class TicTacToeView(View):
    def __init__(
        self,
        player1: discord.User,
        player2: discord.User = None,
        start_shape: str = X_EMOJI,
    ):
        super().__init__(timeout=None)
        if start_shape == X_EMOJI:
            self.player1 = Player(player1, X_EMOJI)
            self.player2 = Player(player2, O_EMOJI)
        elif start_shape == O_EMOJI:
            self.player1 = Player(player1, O_EMOJI)
            self.player2 = Player(player2, X_EMOJI)
        else:
            raise ValueError(f"start_shape can only be {X_EMOJI} or {O_EMOJI}")

        self.current_player = self.player1
        self.message = None
        self.cancel_button = None
        self.moves = 0

        self.grid = []
        for y in range(3):
            row = []
            for x in range(3):
                self.add_item(TicTacToeButton(x, y))
                row.append(EMPTY)
            self.grid.append(row)

        self.cancel_button = Button(label="Cancel", style=ButtonStyle.red)
        self.cancel_button.callback = self.cancel_game
        self.add_item(self.cancel_button)

    async def send_message(self, interaction: discord.Interaction, edit: bool = False):
        embed = discord.Embed(
            color=EMBED_COLOR,
            title="Tic Tac Toe Game",
            description=f"{self.player1} vs {self.player2}",
        )
        embed.add_field(
            name=f"Turn",
            value=self.player1 if self.current_player == self.player1 else self.player2,
        )
        if edit:
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message(embed=embed, view=self)
            self.message = await interaction.original_response()

    async def cancel_game(self, interaction: discord.Interaction):
        if interaction.user == self.player1.user:
            await interaction.message.delete()
        else:
            await interaction.response.send_message(
                f"Only {self.player1.user.mention} can cancel the game", ephemeral=True
            )

    async def update_game(self, interaction: discord.Interaction, player: Player):
        # Check rows, columns, and diagonals for a win
        for i in range(3):
            # Check rows
            if (
                self.grid[i][0] == self.grid[i][1] == self.grid[i][2]
                and self.grid[i][0] != EMPTY
            ):
                await self.end_game(interaction, player)
                return

            # Check columns
            if (
                self.grid[0][i] == self.grid[1][i] == self.grid[2][i]
                and self.grid[0][i] != EMPTY
            ):
                await self.end_game(interaction, player)
                return

        # Check diagonals
        if (
            self.grid[0][0] == self.grid[1][1] == self.grid[2][2]
            and self.grid[0][0] != EMPTY
        ):
            await self.end_game(interaction, player)
            return
        if (
            self.grid[0][2] == self.grid[1][1] == self.grid[2][0]
            and self.grid[0][2] != EMPTY
        ):
            await self.end_game(interaction, player)
            return

        # Check for a draw (tie)
        for row in self.grid:
            if EMPTY in row:
                await self.send_message(interaction, edit=True)
                # add loobi bot support here?
                return

        await self.end_game(interaction, None)

    async def end_game(self, interaction: discord.Interaction, player: Player = None):
        for item in self.children:
            if item.type == discord.ComponentType.button:
                item.disabled = True
        embed = discord.Embed(
            color=EMBED_COLOR,
            title="Tic Tac Toe Game",
            description=f"{self.player1} vs {self.player2}",
        )
        if player is None:
            embed.add_field(name="Tie", value="")
        else:
            embed.add_field(
                name=f"Winner",
                value=player,
            )
        await interaction.response.edit_message(embed=embed, view=self)


@app_commands.command(
    name="tic-tac-toe", description="Play Tic Tac Toe with another member in the server"
)
@app_commands.choices(
    shape=[
        app_commands.Choice(name=X_EMOJI, value=X_EMOJI),
        app_commands.Choice(name=O_EMOJI, value=O_EMOJI),
    ]
)
@app_commands.describe(
    shape="The shape you want to play as",
    opponent="The user you want to play against. Leave empty to make everyone able to play against you",
)
async def game_tic_tac_toe(
    interaction: discord.Interaction,
    shape: str = X_EMOJI,
    opponent: discord.User = None,
):
    # channel check
    if is_in_dm(interaction):
        await must_use_in_guild(interaction)
        return

    # opponent check
    if opponent is not None and opponent.bot:
        await interaction.response.send_message(
            "You can't play against other bots", ephemeral=True
        )
        return

    await TicTacToeView(interaction.user, opponent, shape).send_message(interaction)


async def setup(bot: LoobiBot):
    bot.game_command.add_command(game_tic_tac_toe)

from main import *
from discord.ui import View, Button
from discord import ButtonStyle

X_EMOJI = "❌"
O_EMOJI = "⭕"
EMPTY = "\u200e"
TIE = 0

bot: LoobiBot = None


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

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Player):
            raise ValueError(
                f"Cannot compare between type Player and type {type(value)}"
            )
        return self.user == value.user and self.shape == value.shape


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

        self.grid: list[list[str]] = []
        self.buttons: list[TicTacToeButton] = []
        for y in range(3):
            row = []
            for x in range(3):
                button = TicTacToeButton(x, y)
                self.add_item(button)
                row.append(EMPTY)
                self.buttons.append(button)
            self.grid.append(row)

        self.cancel_button = Button(label="Cancel", style=ButtonStyle.red)
        self.cancel_button.callback = self.cancel_game
        self.add_item(self.cancel_button)

    def get_state(self, grid=None):
        if grid is None:
            grid = self.grid
        # Check rows, columns, and diagonals for a win
        for i in range(3):
            # Check rows
            if grid[i][0] == grid[i][1] == grid[i][2] and grid[i][0] != EMPTY:
                return grid[i][0]

            # Check columns
            if grid[0][i] == grid[1][i] == grid[2][i] and grid[0][i] != EMPTY:
                return grid[0][i]

        # Check diagonals
        if grid[0][0] == grid[1][1] == grid[2][2] and grid[0][0] != EMPTY:
            return grid[0][0]
        if grid[0][2] == grid[1][1] == grid[2][0] and grid[0][2] != EMPTY:
            return grid[0][2]

        # Check for a draw (tie)
        for row in grid:
            if EMPTY in row:
                return None

        return TIE

    async def send_message(
        self, obj: discord.Interaction | discord.Message, edit: bool = False
    ):
        embed = discord.Embed(
            color=EMBED_COLOR,
            title="Tic Tac Toe Game",
            description=f"{self.player1} vs {self.player2}",
        )
        embed.add_field(
            name=f"Turn",
            value=self.player1 if self.current_player == self.player1 else self.player2,
        )
        if isinstance(obj, discord.Message):
            await obj.edit(embed=embed, view=self)
        elif isinstance(obj, discord.Interaction):
            if edit:
                await obj.response.edit_message(embed=embed, view=self)
            else:
                await obj.response.send_message(embed=embed, view=self)
                self.message = await obj.original_response()

    async def cancel_game(self, interaction: discord.Interaction):
        if interaction.user == self.player1.user:
            await interaction.message.delete()
        else:
            await interaction.response.send_message(
                f"Only {self.player1.user.mention} can cancel the game", ephemeral=True
            )

    async def update_game(
        self, obj: discord.Interaction | discord.Message, player: Player
    ):
        state = self.get_state()
        if state is None:  # The game is still going
            # hell yeah bitch
            # TODO: check if oponent is loobi bot, than use a minimax function or something to play
            await self.send_message(obj, edit=True)
            if (
                self.current_player.user is not None
                and self.current_player.user.id == bot.user.id
            ):
                scores = []
                for x, y in tic_tac_toe_range():
                    if self.grid[y][x] != EMPTY:
                        scores.append(-100000)
                    else:
                        scores.append(minimax_magic_shit(self, self.grid, self.player2))
                print(scores)
                index = 0
                for i in range(1, len(scores)):
                    if scores[i] > scores[index]:
                        index = i
                x, y = index % 3, index // 3
                self.buttons[index].emoji = self.current_player.shape
                self.buttons[index].label = None
                self.grid[y][x] = self.current_player.shape
                player = self.current_player
                self.current_player = self.player1
                self.moves += 1
                if self.moves == 2:
                    self.remove_item(self.cancel_button)
                await self.update_game(self.message, player)
        elif state == TIE:
            await self.end_game(obj, None)
        else:
            await self.end_game(obj, player)

    async def end_game(
        self, obj: discord.Interaction | discord.Message, player: Player = None
    ):
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
        if isinstance(obj, discord.Message):
            await obj.edit(embed=embed, view=self)
        elif isinstance(obj, discord.Interaction):
            await obj.response.edit_message(embed=embed, view=self)


def minimax_magic_shit(game: TicTacToeView, grid, current_player: Player):
    # Base case: check if the game has ended
    state = game.get_state(grid)
    if state == game.player1.shape:
        return -1
    elif state == game.player2.shape:
        return 1
    elif state == TIE:
        return 0

    scores = []

    # Loop through all possible moves
    for x, y in tic_tac_toe_range():
        if grid[y][x] != EMPTY:
            scores.append(-100000)
            continue

        # Make a copy of the game state and simulate the move
        next_grid = [[tile for tile in row] for row in grid]
        next_grid[y][x] = current_player.shape

        # Recursive call to minimax for the next player
        score = minimax_magic_shit(
            game,
            next_grid,
            game.player1 if current_player == game.player2 else game.player2,
        )

        # Append the score for the current move
        scores.append(score)

    # Return the maximum score if current player is PLAYER2, else return the minimum score
    if current_player == game.player2:
        return max(scores)
    else:
        return min(scores)


def tic_tac_toe_range():
    for y in range(3):
        for x in range(3):
            yield (x, y)


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
    if opponent is not None and opponent.bot and opponent.id != bot.user.id:
        await interaction.response.send_message(
            "You can't play against other bots", ephemeral=True
        )
        return

    await TicTacToeView(interaction.user, opponent, shape).send_message(interaction)


async def setup(loobibot: LoobiBot):
    global bot
    bot = loobibot
    loobibot.game_command.add_command(game_tic_tac_toe)

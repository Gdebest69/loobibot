import random
from main import *
from discord.ui import View, Button
from discord import ButtonStyle

X_EMOJI = "❌"
O_EMOJI = "⭕"
EMPTY = "\u200e"
TIE = 0

bot: LoobiBot = None
q_table = None


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
            await self.send_message(obj, edit=True)
            # if playing against my bot
            if (
                self.current_player.user is not None
                and self.current_player.user.id == bot.user.id
            ):
                obs = get_obs(self)
                s1 = hash_obs(obs)
                if not s1 in q_table:
                    q_table[s1] = [0] * 9
                    action = random_action(obs)
                else:
                    action = best_action(q_table[s1], obs)
                index = action
                self.buttons[index].emoji = self.current_player.shape
                self.buttons[index].label = None
                self.grid[index // 3][index % 3] = self.current_player.shape
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


def random_action(obs: list[int]):
    """
    Returns a random action in a specific observation
    """
    return random.choice([i for i in range(len(obs)) if obs[i] == 0])


def best_action(q_actions: list[float], obs: list[int]):
    """
    Returns the best action in a specific observation from a Q actions list
    """
    best_action_index = 0
    while obs[best_action_index] != 0:
        best_action_index += 1
    for i in range(best_action_index + 1, len(obs)):
        if obs[i] == 0 and q_actions[i] > q_actions[best_action_index]:
            best_action_index = i
    return best_action_index


def hash_obs(obs: list[int]):
    """
    Hashes the observation so it can be used as a key
    """
    return tuple(obs)


def get_obs(game: TicTacToeView):
    def tile_to_num(tile: str):
        if tile == EMPTY:
            return 0
        if tile == game.player1.shape:
            return 1
        if tile == game.player2.shape:
            return 2

    obs = []
    for row in game.grid:
        for tile in row:
            obs.append(tile_to_num(tile))
    return obs


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
    with open(in_folder("qtable_tic_tac_toe.pkl"), "rb") as file:
        global q_table
        q_table = pickle.load(file)
    global bot
    bot = loobibot
    loobibot.game_command.add_command(game_tic_tac_toe)

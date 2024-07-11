import random
import math
import asyncio
from main import *
from discord.ui import View, Button, Modal, TextInput
from discord import ButtonStyle, TextStyle
from discord.ext import tasks

VALUES = {"J": 10, "Q": 10, "K": 10, "A": 11}
TYPES = {"b": ["eclubs", "espades"], "r": ["ediamonds", "ehearts"]}
MAX_PLAYERS = 7
TURN_TIME = 30
CARD_STACKS = 4
END_GAME_SPEED = 1.5
ICON_SIZE = 128

bot: LoobiBot = None
back_card_top_emoji: discord.Emoji = None
back_card_bottom_emoji: discord.Emoji = None
all_crads: list["Card"] = []
upcoming_games: dict[int, "UpcomingGame"] = {}
blackjack_games: dict[int, "BlackjackGame"] = {}


class Card:
    def __init__(
        self,
        value: str,
        type: str,
        top_emoji: discord.Emoji,
        bottom_emoji: discord.Emoji,
        hidden: bool = False,
    ) -> None:
        self.value = value
        self.type = type
        self.top_emoji = top_emoji
        self.bottom_emoji = bottom_emoji
        self.hidden = hidden

    def get_value(self):
        if self.value.isdigit():
            return int(self.value)
        else:
            return VALUES[self.value]

    def copy(self):
        return Card(
            self.value, self.type, self.top_emoji, self.bottom_emoji, self.hidden
        )

    def get_top(self):
        if self.hidden:
            return str(back_card_top_emoji)
        return str(self.top_emoji)

    def get_bottom(self):
        if self.hidden:
            return str(back_card_bottom_emoji)
        return str(self.bottom_emoji)

    def __str__(self) -> str:
        if self.hidden:
            return f"{back_card_top_emoji}\n{back_card_bottom_emoji}"
        return f"{self.top_emoji}\n{self.bottom_emoji}"


class PlayCards:
    def __init__(self, money_bet: int, start_cards: tuple[Card, Card]) -> None:
        self.money_bet = money_bet
        self.cards = [start_cards[0], start_cards[1]]
        self.doubled = False
        self.surrended = False

    def get_value(self):
        value = 0
        for card in self.cards:
            value += card.get_value()
        # convert aces to 1 if necessary
        if value > 21:
            aces = 0
            for card in self.cards:
                if card.value == "A":
                    aces += 1
            dnormal = ((value - 21) // 10 + 1) * 10
            dmax = aces * 10
            d = min(dnormal, dmax)
            value -= d
        return value

    def get_money_bet(self):
        if self.doubled:
            return self.money_bet * 2
        if self.surrended:
            return int(math.ceil(self.money_bet / 2))
        return self.money_bet

    def get_state(self, dealer_cards: "PlayCards" = None):
        if self.blackjack():
            return (
                0
                if dealer_cards is not None and dealer_cards.blackjack()
                else int(math.floor(self.get_money_bet() * 1.5))
            )
        dealer_value = dealer_cards.get_value() if dealer_cards is not None else -1
        if (
            self.surrended
            or self.get_value() > 21
            or (dealer_value > self.get_value() and dealer_value <= 21)
        ):
            return -self.get_money_bet()
        if dealer_value == self.get_value():
            return 0
        return self.get_money_bet()

    def can_hit(self):
        if self.doubled:
            return len(self.cards) <= 1
        else:
            return self.get_value() <= 21

    def can_split(self):
        return len(self.cards) == 2 and self.cards[0].value == self.cards[1].value

    def can_double(self):
        return len(self.cards) == 2 and not self.doubled

    def blackjack(self):
        return len(self.cards) == 2 and self.get_value() == 21

    def add_card(self, card: Card):
        self.cards.append(card)

    def __str__(self) -> str:
        row1 = " ".join([card.get_top() for card in self.cards])
        if discord.utils.get(self.cards, hidden=True) is None:
            row1 += f" ({self.get_value()})"
        if self.money_bet > 0:
            prefix = " +" if self.blackjack() else " "
            money = money_str(self.get_state())
            row1 += prefix + money
        row2 = " ".join([card.get_bottom() for card in self.cards])
        if self.doubled:
            row2 += " Doubled"
        elif self.blackjack():
            row2 += " Blackjack"
        return row1 + "\n" + row2

    def str_at_end(self, dealer_cards: "PlayCards"):
        row1 = " ".join([card.get_top() for card in self.cards])
        if discord.utils.get(self.cards, hidden=True) is None:
            row1 += f" ({self.get_value()})"
        if self.money_bet > 0:
            state = self.get_state(dealer_cards)
            prefix = " +" if state >= 0 else " "
            money = prefix + money_str(state)
            row1 += money
        row2 = " ".join([card.get_bottom() for card in self.cards])
        if self.doubled:
            row2 += " Doubled"
        elif self.blackjack():
            row2 += " Blackjack"
        return row1 + "\n" + row2


class UpcomingPlayer:
    def __init__(self, user: discord.User, money_bet: int) -> None:
        self.user = user
        self.money_bet = money_bet

    def __str__(self) -> str:
        return money_str(self.money_bet) + " " + self.user.mention

    def __eq__(self, __value: object) -> bool:
        return self.user.id == __value.id


class Player:
    def __init__(
        self, user: discord.User, money_bet: int, start_cards: tuple[Card, Card]
    ) -> None:
        self.user = user
        self.cards = [PlayCards(money_bet, start_cards)]

    def to_embed_field(self, play_cards_index: int = -1):
        name = self.user.display_name
        value = "\n".join(
            [
                f"**{str(play_cards)}**" if i == play_cards_index else str(play_cards)
                for i, play_cards in enumerate(self.cards)
            ]
        )
        return {"name": name, "value": value, "inline": True}

    def end_to_embed_field(self, dealer_cards: "PlayCards"):
        name = self.user.display_name
        value = "\n".join(
            [play_cards.str_at_end(dealer_cards) for play_cards in self.cards]
        )
        return {"name": name, "value": value, "inline": True}

    def __str__(self) -> str:
        return self.user.mention


class UpcomingGame(View):
    def __init__(
        self,
        host: UpcomingPlayer,
        cards: list[Card] = None,
        used_cards: list[Card] = None,
    ):
        super().__init__(timeout=None)
        self.host = host
        self.players = [host]
        self.message = None

        if cards is None:
            cards = create_card_stack()
        if used_cards is None:
            used_cards = []
        self.cards = cards
        self.used_cards = used_cards

        self.check_message.start()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # update user data if missing
        if bot.get_user_data(interaction.user.id) is None:
            bot.set_user_data(interaction.user.id, UserData())
        return True

    @discord.ui.button(
        label="Start", style=ButtonStyle.blurple, custom_id="upcoming_game"
    )
    async def start_game(self, interaction: discord.Interaction, button: Button):
        if interaction.user == self.host.user:
            upcoming_games.pop(self.message.id)
            await BlackjackGame(
                self.players, self.cards, self.used_cards, self.message
            ).send_message(interaction)
        else:
            await interaction.response.send_message(
                f"Only {self.host.user.mention} can start the game", ephemeral=True
            )

    @discord.ui.button(label="Join", style=ButtonStyle.green)
    async def join_game(self, interaction: discord.Interaction, button: Button):
        if len(self.players) >= MAX_PLAYERS:
            await interaction.response.send_message("This game is full", ephemeral=True)
            return

        user_money = bot.get_user_data(interaction.user.id).money
        if user_money <= 0:
            await interaction.response.send_message(
                "You don't have any money", ephemeral=True
            )
            return

        if interaction.user in self.players:
            await interaction.response.send_message(
                "You already joined", ephemeral=True
            )
        else:
            await interaction.response.send_modal(JoinGameModal(interaction.user, self))

    @discord.ui.button(label="Leave", style=ButtonStyle.red)
    async def leave_game(self, interaction: discord.Interaction, button: Button):
        if interaction.user == self.host.user:
            await interaction.message.delete()
            return
        if interaction.user in self.players:
            bot.get_user_data(interaction.user.id).money += discord.utils.get(
                self.players, user=interaction.user
            ).money_bet
            self.players.remove(interaction.user)
        else:
            await interaction.response.send_message(
                "You are not in the game", ephemeral=True
            )
            return
        if not self.players:
            await interaction.message.delete()
        else:
            await self.send_message(interaction, True)

    async def send_message(self, interaction: discord.Interaction, edit: bool = False):
        embed = discord.Embed(
            color=EMBED_COLOR,
            title=f"Blackjack {len(self.players)}/{MAX_PLAYERS}",
            description=f"Requested by {self.host.user.mention}",
        )
        if self.players:
            embed.add_field(
                name="Players",
                value="\n".join(
                    [
                        str(player)
                        for player in sorted(
                            self.players, reverse=True, key=lambda x: x.money_bet
                        )
                    ]
                ),
            )
        if edit:
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message(embed=embed, view=self)
            self.message = await interaction.original_response()
            upcoming_games[self.message.id] = self

    @tasks.loop(seconds=30)
    async def check_message(self):
        # print("call")
        if self.message is not None:
            try:
                await self.message.channel.fetch_message(self.message.id)
            except:
                self.check_message.stop()
                await on_message_delete(self.message)
                # print("stop")


class BlackjackGame(View):
    def __init__(
        self,
        upcoming_players: list[UpcomingPlayer],
        cards: list[Card],
        used_cards: list[Card],
        message: discord.Message,
        *,
        dealer_cards=None,
        players=None,
        turn_index=None,
        play_cards_index=None,
        ending=None,
    ):
        super().__init__(timeout=TURN_TIME)
        self.cards = cards
        self.used_cards = used_cards
        self.message = message

        if dealer_cards is None:
            hidden_card = self.pull_card_from_stack().copy()
            hidden_card.hidden = True
            self.dealer_cards = PlayCards(
                -1, (hidden_card, self.pull_card_from_stack())
            )
        else:
            self.dealer_cards = dealer_cards

        if players is None:
            self.players = [
                Player(
                    player.user,
                    player.money_bet,
                    (self.pull_card_from_stack(), self.pull_card_from_stack()),
                )
                for player in upcoming_players
            ]
        else:
            self.players = players

        self.turn_index = 0 if turn_index is None else turn_index
        self.play_cards_index = 0 if play_cards_index is None else play_cards_index
        self.ending = False if ending is None else ending
        blackjack_games[self.message.id] = self

        self.hit_button = Button(label="Hit", style=ButtonStyle.green)
        self.hit_button.callback = self.hit
        self.add_item(self.hit_button)

        self.stand_button = Button(label="Stand", style=ButtonStyle.gray)
        self.stand_button.callback = self.stand
        self.add_item(self.stand_button)

        self.surrender_button = Button(label="Surrender", style=ButtonStyle.red)
        self.surrender_button.callback = self.surrender
        self.add_item(self.surrender_button)

        self.double_button = Button(label="Double", row=1, style=ButtonStyle.blurple)
        self.double_button.callback = self.double
        self.add_item(self.double_button)

        self.split_button = Button(label="Split", row=1, style=ButtonStyle.blurple)
        self.split_button.callback = self.split
        self.add_item(self.split_button)

    def pull_card_from_stack(self):
        if not self.cards:
            random.shuffle(self.used_cards)
            self.cards = self.used_cards
            self.used_cards = []
        card = self.cards.pop(0)
        self.used_cards.append(card)
        return card

    def get_current_player(self):
        return self.players[self.turn_index]

    def get_curent_play_cards(self):
        return self.get_current_player().cards[self.play_cards_index]

    def give_money(self, forced: bool = False):
        for player in self.players:
            user_data = bot.get_user_data(player.user.id)
            for play_cards in player.cards:
                user_data.money += play_cards.get_money_bet()
                if not forced:
                    user_data.money += play_cards.get_state(self.dealer_cards)
                elif play_cards.get_state() < 0 or play_cards.blackjack():
                    user_data.money += play_cards.get_state()

    async def send_message(
        self,
        ctx: discord.Interaction | discord.Message,
        end: bool = False,
        stop: bool = False,
    ):
        try:
            if self.dealer_cards.blackjack():
                self.dealer_cards.cards[0].hidden = False
                end = True
            if end:
                embed = discord.Embed(
                    color=EMBED_COLOR,
                    title="Blackjack game",
                    description=f"Turn: Dealer",
                )
                embed.set_thumbnail(url=bot.user.display_avatar.with_size(ICON_SIZE))
                embed.add_field(name="Dealer", value=self.dealer_cards, inline=False)

                if stop:
                    for player in self.players:
                        embed.add_field(**player.end_to_embed_field(self.dealer_cards))
                else:
                    for player in self.players:
                        embed.add_field(**player.to_embed_field())

                self.hit_button.disabled = True
                self.split_button.disabled = True
                self.stand_button.disabled = True
                self.double_button.disabled = True
                self.surrender_button.disabled = True

                if stop:
                    await self.message.edit(
                        embed=embed,
                        view=EndGameView(
                            self.players[0], self.cards, self.used_cards, self.message
                        ),
                    )
                else:
                    if isinstance(ctx, discord.Interaction):
                        await ctx.response.edit_message(embed=embed, view=self)
                    elif isinstance(ctx, discord.Message):
                        await ctx.edit(embed=embed, view=self)
                    if not self.ending:
                        self.ending = True
                        await self.end_game()
            else:
                if self.get_curent_play_cards().get_value() == 21:
                    await self.stand(ctx)
                    return
                embed = discord.Embed(
                    color=EMBED_COLOR,
                    title="Blackjack game",
                    description=f"Turn: {self.get_current_player()}",
                )
                embed.set_thumbnail(
                    url=self.get_current_player().user.display_avatar.with_size(
                        ICON_SIZE
                    )
                )
                embed.add_field(name="Dealer", value=self.dealer_cards, inline=False)

                for i, player in enumerate(self.players):
                    if i == self.turn_index:
                        embed.add_field(**player.to_embed_field(self.play_cards_index))
                    else:
                        embed.add_field(**player.to_embed_field())

                play_cards = self.get_curent_play_cards()
                self.hit_button.disabled = not play_cards.can_hit()
                self.split_button.disabled = not play_cards.can_split()
                self.double_button.disabled = not play_cards.can_double()

                if isinstance(ctx, discord.Interaction):
                    await ctx.response.edit_message(embed=embed, view=self)
                elif isinstance(ctx, discord.Message):
                    await ctx.edit(embed=embed, view=self)

        except discord.errors.NotFound:
            if self.message.id in blackjack_games:
                cancel_game(blackjack_games[self.message.id])
                blackjack_games.pop(self.message.id)

    async def next_player(self, interaction: discord.Interaction | discord.Message):
        self.turn_index += 1
        if self.turn_index >= len(self.players):
            self.stop()
            await self.send_message(interaction, end=True)
        else:
            await self.send_message(interaction)

    async def hit(self, interaction: discord.Interaction):
        play_cards = self.get_curent_play_cards()
        play_cards.add_card(self.pull_card_from_stack())
        if not play_cards.can_hit():
            await self.stand(interaction)
        else:
            await self.send_message(interaction)

    async def stand(self, interaction: discord.Interaction):
        self.play_cards_index += 1
        if self.play_cards_index >= len(self.get_current_player().cards):
            self.play_cards_index = 0
            await self.next_player(interaction)
        else:
            await self.send_message(interaction)

    async def double(self, interaction: discord.Interaction):
        money_bet = self.get_curent_play_cards().get_money_bet()
        user_money = bot.get_user_data(interaction.user.id).money
        if money_bet > user_money:
            await interaction.response.send_message(
                "You don't have enough money to double", ephemeral=True
            )
            return

        bot.get_user_data(interaction.user.id).money -= money_bet
        play_cards = self.get_curent_play_cards()
        play_cards.doubled = True
        play_cards.add_card(self.pull_card_from_stack())
        await self.stand(interaction)

    async def split(self, interaction: discord.Interaction):
        modal = JoinGameModal(interaction.user, self)
        modal.title = "Split cards"
        await interaction.response.send_modal(modal)

    async def surrender(self, interaction: discord.Interaction):
        play_cards = self.get_curent_play_cards()
        bot.get_user_data(interaction.user.id).money += (
            self.get_curent_play_cards().get_money_bet() // 2
        )
        play_cards.surrended = True
        await self.stand(interaction)

    async def end_game(self):
        self.dealer_cards.cards[0].hidden = False
        await asyncio.sleep(END_GAME_SPEED)
        await self.send_message(self.message, end=True)
        while self.dealer_cards.get_value() < 17:
            self.dealer_cards.add_card(self.pull_card_from_stack())
            await asyncio.sleep(END_GAME_SPEED)
            await self.send_message(self.message, end=True)
        if self.message.id in blackjack_games:
            self.give_money()
            blackjack_games.pop(self.message.id)
        await self.send_message(None, end=True, stop=True)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.get_current_player().user.id:
            return True
        await interaction.response.send_message(
            f"Only {self.get_current_player()} can use this", ephemeral=True
        )
        return False

    async def on_timeout(self) -> None:
        # print("timeout, next user")
        if self.message.id in blackjack_games:
            view = BlackjackGame(
                None,
                self.cards,
                self.used_cards,
                self.message,
                dealer_cards=self.dealer_cards,
                players=self.players,
                turn_index=self.turn_index,
                play_cards_index=self.play_cards_index,
                ending=self.ending,
            )
            await view.next_player(view.message)


class EndGameView(View):
    def __init__(
        self,
        host: Player,
        cards: list[Card],
        used_cards: list[Card],
        message: discord.Message,
    ):
        super().__init__(timeout=TIMEOUT)
        self.host = host.user
        self.cards = cards
        self.used_cards = used_cards
        self.message = message

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.host.id:
            return True
        await interaction.response.send_message(
            f"Only {self.host.mention} can use this", ephemeral=True
        )
        return False

    @discord.ui.button(label="Continue", style=ButtonStyle.green)
    async def continue_game(self, interaction: discord.Interaction, button: Button):
        user_money = bot.get_user_data(interaction.user.id).money
        if user_money <= 0:
            await interaction.response.send_message(
                "You don't have any money", ephemeral=True
            )
            return

        await interaction.response.send_modal(
            JoinGameModal(self.host, self, self.cards, self.used_cards)
        )

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.blurple)
    async def stop_game(self, interaction: discord.Interaction, button: Button):
        await interaction.message.edit(view=None)

    async def on_timeout(self) -> None:
        await self.message.edit(view=None)


class JoinGameModal(Modal):
    def __init__(
        self,
        user: discord.User,
        view: UpcomingGame | BlackjackGame | EndGameView = None,
        cards: list[Card] = None,
        used_cards: list[Card] = None,
    ) -> None:
        super().__init__(title="Join Blackjack", timeout=None)
        self.view = view
        self.cards = cards
        self.used_cards = used_cards
        self.bet = TextInput(
            label="Your bet",
            style=TextStyle.short,
            placeholder=f"{bot.get_user_data(user.id).money}$",
            min_length=1,
            max_length=6,
        )
        self.add_item(self.bet)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if isinstance(self.view, UpcomingGame):
            if len(self.view.players) >= MAX_PLAYERS:
                await interaction.response.send_message(
                    "This game is full", ephemeral=True
                )
                return

            if interaction.message.id not in upcoming_games:
                await interaction.response.send_message(
                    "This game already started", ephemeral=True
                )
                return

        if (
            isinstance(self.view, BlackjackGame)
            and interaction.user.id != self.view.get_current_player().user.id
        ):
            await interaction.response.send_message(
                "This is not your turn", ephemeral=True
            )
            return

        # input check
        bet_money = self.bet.value
        if bet_money.endswith("$"):
            bet_money = bet_money[:-1]
        if not bet_money.isdigit():
            await interaction.response.send_message("Invalid amount", ephemeral=True)
            return
        bet_money = int(bet_money)
        if not bet_money > 0:
            await interaction.response.send_message(
                "You must bet at least 1$", ephemeral=True
            )
            return

        # money check
        if bot.get_user_data(interaction.user.id).money < bet_money:
            await interaction.response.send_message(
                "You don't have enough money", ephemeral=True
            )
            return

        bot.get_user_data(interaction.user.id).money -= bet_money

        if self.view is None:
            player = UpcomingPlayer(interaction.user, bet_money)
            await UpcomingGame(player, self.cards, self.used_cards).send_message(
                interaction
            )
        elif isinstance(self.view, UpcomingGame):
            player = UpcomingPlayer(interaction.user, bet_money)
            self.view.players.append(player)
            await self.view.send_message(interaction, True)
        elif isinstance(self.view, BlackjackGame):
            player = self.view.get_current_player()
            player.cards.append(
                PlayCards(
                    bet_money,
                    (
                        self.view.get_curent_play_cards().cards[1],
                        self.view.pull_card_from_stack(),
                    ),
                )
            )
            self.view.get_curent_play_cards().cards[
                1
            ] = self.view.pull_card_from_stack()
            await self.view.send_message(interaction)
        elif isinstance(self.view, EndGameView):
            player = UpcomingPlayer(interaction.user, bet_money)
            await self.view.message.edit(view=None)
            await UpcomingGame(player, self.cards, self.used_cards).send_message(
                interaction
            )


def create_card_stack():
    cards = []
    for _ in range(CARD_STACKS):
        cards += [card.copy() for card in all_crads]
    random.shuffle(cards)
    return cards


def create_default_card_stack(emojis: list[discord.Emoji]):
    card_stack = []
    for emoji in emojis:
        color = emoji.name[0]
        if color in TYPES:
            value = emoji.name[1:]
            for type in TYPES[color]:
                card = Card(value, type, emoji, discord.utils.get(emojis, name=type))
                card_stack.append(card)
    return card_stack


def cancel_upcoming_game(game: UpcomingGame):
    game.stop()
    for player in game.players:
        bot.get_user_data(player.user.id).money += player.money_bet


def cancel_game(game: BlackjackGame):
    game.stop()
    game.give_money(forced=True)


@app_commands.command(
    name="blackjack",
    description="Play and bet in Blackjack with other members in the server",
)
async def game_blackjack(interaction: discord.Interaction):
    # channel check
    if is_in_dm(interaction):
        await must_use_in_guild(interaction)
        return

    user_money = bot.get_user_data(interaction.user.id).money
    if user_money <= 0:
        await interaction.response.send_message(
            "You don't have any money", ephemeral=True
        )
        return

    await interaction.response.send_modal(JoinGameModal(interaction.user))


@commands.Cog.listener()
async def on_message_edit(before: discord.Message, after: discord.Message):
    if not after.embeds:
        if after.id in upcoming_games:
            await upcoming_games[after.id].message.delete()
        if after.id in blackjack_games:
            await blackjack_games[after.id].message.delete()


@commands.Cog.listener()
async def on_message_delete(message: discord.Message):
    if message.id in upcoming_games:
        cancel_upcoming_game(upcoming_games[message.id])
        upcoming_games.pop(message.id)
    if message.id in blackjack_games:
        cancel_game(blackjack_games[message.id])
        blackjack_games.pop(message.id)


@tasks.loop(seconds=2.5)
async def test():
    print(upcoming_games, blackjack_games, sep="\n", end="\n\n")


async def setup(loobibot: LoobiBot):
    global bot
    bot = loobibot
    # Upload emojis
    emojis_guild = loobibot.get_guild(TEST_GUILD_ID)
    crads_dir = in_folder(os.path.join("assets", "cards"))
    emoji_list = []
    for file in os.listdir(crads_dir):
        card_name = os.path.splitext(file)[0]
        emoji = discord.utils.get(emojis_guild.emojis, name=card_name)
        if emoji is None:
            with open(os.path.join(crads_dir, file), "rb") as image:
                emoji = await emojis_guild.create_custom_emoji(
                    name=card_name, image=image.read()
                )
                loobibot.logger.info(f"Created {emoji.name} emoji")
        emoji_list.append(emoji)

    global all_crads
    all_crads = create_default_card_stack(emoji_list)

    global back_card_top_emoji, back_card_bottom_emoji
    back_card_top_emoji = discord.utils.get(emojis_guild.emojis, name="eblankbacktop")
    back_card_bottom_emoji = discord.utils.get(
        emojis_guild.emojis, name="eblankbackbot"
    )

    loobibot.game_command.add_command(game_blackjack)
    loobibot.add_listener(on_message_edit)
    loobibot.add_listener(on_message_delete)

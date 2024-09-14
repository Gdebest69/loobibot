import random
from discord.ext import tasks
from main import *


class Picasion(commands.Cog):
    def __init__(self, bot: LoobiBot):
        self.bot = bot
        self.gay_ids = [
            721293202656591923,  # dani
            782364402313068594,  # vistia
        ]
        self.allowed_guild_ids = [
            861213619000573972,  # test server
            1187846300071375029,  # dani server
        ]
        self.qr_size = 175
        self.delete_message_chance = 0.25
        self.disconnect_chance = 0.25

        self.disconnect_task.start()

    async def cog_check(self, ctx: commands.Context) -> bool:
        return ctx.guild and ctx.guild.id in self.allowed_guild_ids

    @commands.command(name="help")
    async def help_command(self, ctx: commands.Context):
        await ctx.reply(
            "**Commands:**\n\n"
            "**!hello** - Say hello\n"
            "**!invite** - Get invite link\n"
            "**!say** - Say something\n"
            "**!gay** - Say if you are gay or not\n"
            "**!coinflip** - Select a random choice of tails or heads\n"
            "**!qr** - Create a QR code\n"
            "**!guess** - Guess a number from 1 to 10\n"
            "**!tictactoe** - Play tictactoe vs a friend",
            mention_author=False,
        )

    @commands.command(name="hello", description="Say hello")
    async def hello_command(self, ctx: commands.Context):
        await ctx.channel.send("Hello")

    @commands.command(name="invite", description="Get invite link")
    async def invite_command(self, ctx: commands.Context):
        # not using discord.utils.oauth_url because it adds scopes
        await ctx.reply(
            "https://discord.com/oauth2/authorize?client_id=993476730452983839",
            mention_author=False,
        )

    @commands.command(name="say", description="Say something")
    async def say_command(self, ctx: commands.Context, *, message):
        await ctx.reply(message, mention_author=False, delete_after=TEMP_MESSAGE_SEC)

    @commands.command(name="gay", description="Say if you are gay or not")
    async def gay_command(self, ctx: commands.Context):
        message = "you are gay" if ctx.author.id in self.gay_ids else "you are not gay"
        await ctx.reply(message, mention_author=False)

    @commands.command(
        name="coinflip", description="Select a random choice of tails or heads"
    )
    async def coinflip_command(self, ctx: commands.Context):
        message = random.choice(["heads", "tails"])
        await ctx.reply(message)

    @commands.command(name="qr", description="Create a QR code")
    async def qr_command(self, ctx: commands.Context, *, url):
        await ctx.reply(
            f"https://api.qrserver.com/v1/create-qr-code/?size={self.qr_size}x{self.qr_size}&data={url}",
            mention_author=False,
        )

    @commands.command(name="guess", description="Guess a number from 1 to 10")
    async def guess_command(self, ctx: commands.Context):
        number = random.randint(1, 10)
        channel = ctx.channel
        await channel.send("Guess a number between 1 and 10. Type your answer!")

        def check(m):
            return m.channel == channel and m.author == ctx.author

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=30)
        except TimeoutError:
            await channel.send("Time's up!")
            return

        try:
            guessed_number = int(msg.content)
        except ValueError:
            await channel.send("That's not a number!")
            return

        if guessed_number == number:
            await channel.send("Correct! You guessed the number.")
        else:
            await channel.send(f"Incorrect. The number was {number}.")

    @commands.command("tictactoe", description="Play tictactoe vs a friend")
    async def tictactoe_command(self, ctx: commands.Context):
        await ctx.reply("/game tic-tac-toe", mention_author=False)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if (
            message.guild
            and message.guild.id in self.allowed_guild_ids
            and random.random() < self.delete_message_chance
        ):
            try:
                await message.delete()
            except discord.Forbidden:
                await (await self.bot.fetch_user(OWNER_ID)).send(
                    "Can't delete message: " + message.jump_url
                )

    @tasks.loop(minutes=5, reconnect=True)
    async def disconnect_task(self):
        for guild_id in self.allowed_guild_ids:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                continue
            for channel in guild.channels:
                if channel.type != discord.ChannelType.voice:
                    continue
                for member in channel.members:
                    if random.random() > self.disconnect_chance:
                        continue
                    try:
                        await member.edit(voice_channel=None)
                    except discord.Forbidden:
                        await (await self.bot.fetch_user(OWNER_ID)).send(
                            f"Can't disconnect member {member} from channel {channel}"
                        )


async def setup(bot: LoobiBot):
    await bot.add_cog(Picasion(bot))

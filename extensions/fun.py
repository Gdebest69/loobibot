from main import *


class FunStuff(commands.Cog):
    def __init__(self, bot: LoobiBot):
        self.bot = bot
        self.reach_id = 294452820353089536
        self.ok_channel_id = 1264654642374115328
        self.ok_message = "ok"

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Delete any message containing a link to pokemonshowdown.com from reach
        if (
            message.guild is not None
            and message.guild.id == GUILD_ID
            and "pokemonshowdown.com" in message.content
            and message.author.id == self.reach_id
        ):
            print_message(message, self.bot.logger)
            await message.delete()

        # Delete any message in the ok channel that doesn't contain "ok"
        if (
            is_in_guild(message)
            and message.channel.id == self.ok_channel_id
            and plain_message(message.content).lower() != self.ok_message
        ):
            print_message(message, self.bot.logger)
            try:
                await message.delete()
                await message.author.send("Not ok")
            except discord.Forbidden:
                pass

        # yeshuagay5
        if plain_message(message.content).lower() == "gay":
            print_message(message, self.bot.logger)
            await message.reply(f"Just like yeshua")
        elif plain_message(message.content).lower() == "hella gay":
            await message.reply(f"Totally Yeshua")
        elif plain_message(message.content).lower() == "furry":
            await message.reply(
                file=discord.File(in_folder(os.path.join("assets", "furry.png")))
            )


async def setup(bot: LoobiBot):
    await bot.add_cog(FunStuff(bot))

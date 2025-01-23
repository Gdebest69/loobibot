from main import *


class OkCheck(commands.Cog):
    def __init__(self, bot: LoobiBot):
        self.bot = bot
        self.channel_id = 1264654642374115328
        self.ok_message = "ok"

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if (
            is_in_guild(message)
            and message.channel.id == self.channel_id
            and message.content.lower() != self.ok_message
        ):
            try:
                await message.delete()
                await message.author.send("Not ok")
            except discord.Forbidden:
                pass


async def setup(bot: LoobiBot):
    await bot.add_cog(OkCheck(bot), guild=discord.Object(MIXED_LOUNGE_GUILD_ID))

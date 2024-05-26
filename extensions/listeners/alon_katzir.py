from main import *


class WeDoSomeLols(commands.Cog):
    def __init__(self, bot: LoobiBot):
        self.bot = bot
        self.reach_id = 294452820353089536

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if (
            message.guild is not None
            and message.guild.id == GUILD_ID
            and "pokemonshowdown.com" in message.content
            and message.author.id == self.reach_id
        ):
            await message.delete()


async def setup(bot: LoobiBot):
    await bot.add_cog(WeDoSomeLols(bot))

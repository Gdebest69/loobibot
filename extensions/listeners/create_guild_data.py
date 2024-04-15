from main import *


class CreateGuildData(commands.Cog):
    def __init__(self, bot: LoobiBot):
        self.bot = bot
        for guild in self.bot.guilds:
            self.create_guild_data(guild)

    def create_guild_data(self, guild: discord.Guild):
        if self.bot.get_guild_data(guild.id) is None:
            self.bot.set_guild_data(guild.id, GuildData())

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        self.create_guild_data(guild)


async def setup(bot: LoobiBot):
    await bot.add_cog(CreateGuildData(bot))

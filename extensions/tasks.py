import datetime
from discord.ext import tasks
from main import *


class Tasks(commands.Cog):
    def __init__(self, bot: LoobiBot):
        self.bot = bot
        if not bot.testing:
            self.auto_save_data.start()

    @tasks.loop(seconds=SAVE_TIME_SEC, reconnect=True)
    async def auto_save_data(self):
        self.bot.save_data()


async def setup(bot: LoobiBot):
    await bot.add_cog(Tasks(bot))

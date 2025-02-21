import datetime
from discord.ext import tasks
from main import *


class Tasks(commands.Cog):
    def __init__(self, bot: LoobiBot):
        self.bot = bot
        self.current_color = len(RGB_COLORS) - 1
        if not bot.testing:
            self.auto_save_data.start()
            self.rgb_effect.start()

    @tasks.loop(seconds=SAVE_TIME_SEC, reconnect=True)
    async def auto_save_data(self):
        self.bot.save_data()

    @tasks.loop(seconds=RGB_EFFECT_COOL_DOWN_SEC, reconnect=True)
    async def rgb_effect(self):
        if self.current_color >= len(RGB_COLORS) - 1:
            self.current_color = 0
        else:
            self.current_color += 1
        role = self.bot.get_guild(GUILD_ID).get_role(RGB_ROLE_ID)
        await role.edit(color=discord.Color(RGB_COLORS[self.current_color]))


async def setup(bot: LoobiBot):
    await bot.add_cog(Tasks(bot))

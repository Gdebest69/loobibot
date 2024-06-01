import datetime
from discord.ext import tasks
from main import *


class Tasks(commands.Cog):
    def __init__(self, bot: LoobiBot):
        self.bot = bot
        self.rgb = False
        self.current_color = len(RGB_COLORS) - 1
        if not bot.testing:
            self.auto_save_data.start()

    @tasks.loop(hours=1)
    async def exercise_reminder(self):
        vacation_range = (datetime.time(10), datetime.time(20))
        ranges = {
            0: (datetime.time(15), datetime.time(20)),  # Monday
            1: (datetime.time(13), datetime.time(20)),  # Tuesday
            2: (datetime.time(16, 30), datetime.time(20)),  # Wednesday
            3: (datetime.time(17, 30), datetime.time(20)),  # Thursday
            4: (datetime.time(10, 0), datetime.time(20)),  # Friday
            5: (datetime.time(10, 0), datetime.time(19, 30)),  # Saturday
            6: (datetime.time(17, 30), datetime.time(20)),  # Sunday
        }
        user_id = OWNER_ID

        user = self.bot.get_user(user_id)
        week_day = datetime.datetime.now().weekday()
        if not week_day in ranges:
            return

        today_range = vacation_range if self.bot.vacation else ranges[week_day]
        now = datetime.datetime.now().time()
        if today_range[0] < now < today_range[1]:
            await user.send(EXERCISE_MESSAGE)

    @tasks.loop(seconds=SAVE_TIME_SEC)
    async def auto_save_data(self):
        self.bot.save_data()

        if not self.rgb:
            if self.rgb_effect.is_running():
                self.rgb_effect.stop()
                self.rgb_effect.start()
            else:
                self.rgb_effect.start()

        """if not self.exercise_reminder.is_running():
            self.exercise_reminder.start()"""

        self.rgb = False

    @tasks.loop(seconds=RGB_EFFECT_COOL_DOWN_SEC)
    async def rgb_effect(self):
        if self.current_color >= len(RGB_COLORS) - 1:
            self.current_color = 0
        else:
            self.current_color += 1
        role = self.bot.get_guild(GUILD_ID).get_role(RGB_ROLE_ID)
        await role.edit(color=discord.Color(RGB_COLORS[self.current_color]))
        self.rgb = True


async def setup(bot: LoobiBot):
    await bot.add_cog(Tasks(bot))

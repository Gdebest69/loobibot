from main import *


class GiveDJRole(commands.Cog):
    def __init__(self, bot: LoobiBot):
        self.bot = bot

    async def give_dj_role(self, member: discord.Member):
        guild_data = self.bot.get_guild_data(member.guild.id)
        if has_one_of_roles(member, guild_data.dj_roles_id, ignore_admin=True):
            dj_role = self.bot.music.get_dj_role(member.guild)
            if dj_role is not None and not has_role(member, dj_role.id):
                try:
                    await member.add_roles(dj_role, reason="DJ role")
                except discord.Forbidden:
                    pass

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if not is_in_dm(message):
            await self.give_dj_role(message.author)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        await self.give_dj_role(after)


async def setup(bot: LoobiBot):
    await bot.add_cog(GiveDJRole(bot))

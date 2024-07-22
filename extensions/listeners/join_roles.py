from main import *


class JoinRoles(commands.Cog):
    def __init__(self, bot: LoobiBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        # save roles
        roles_id_list = []
        for role in member.roles:
            roles_id_list.append(role.id)
        roles_id_list.remove(member.guild.default_role.id)
        self.bot.get_guild_data(member.guild.id).roles[member.id] = roles_id_list

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        # add saved roles
        guild = member.guild
        guild_saved_roles = self.bot.get_guild_data(guild.id).roles
        if member.id in guild_saved_roles:
            for role_id in guild_saved_roles[member.id]:
                role = guild.get_role(role_id)
                if role is not None:
                    try:
                        await member.add_roles(role, reason="Auto roles")
                    except discord.Forbidden:
                        pass
            self.bot.logger.info(f"Added saved roles for {member} in {member.guild}")


async def setup(bot: LoobiBot):
    await bot.add_cog(JoinRoles(bot))

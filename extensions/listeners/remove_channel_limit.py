from main import *


class RemoveChannelLimit(commands.Cog):
    def __init__(self, bot: LoobiBot):
        self.bot = bot
        self.channel_limits: dict[int, int] = {}

    def get_human_members(self, channel: discord.VoiceChannel):
        """Counts how many non bot users are in a voice channel"""
        counter = 0
        for member in channel.members:
            if not member.bot:
                counter += 1
        return counter

    async def handle_channel(self, channel: discord.VoiceChannel):
        # check if the channel limit has been exceeded
        if (
            channel.id not in self.channel_limits
            and 0 < channel.user_limit < self.get_human_members(channel)
        ):
            try:
                limit = channel.user_limit
                await channel.edit(
                    user_limit=0, reason="Remove channel user limit temporarily"
                )
                self.channel_limits[channel.id] = limit
            except discord.Forbidden:
                pass

        # check if the channel limit has returned to normal
        if (
            channel.id in self.channel_limits
            and self.get_human_members(channel) <= self.channel_limits[channel.id]
        ):
            try:
                await channel.edit(
                    user_limit=self.channel_limits[channel.id],
                    reason="Restore channel user limit",
                )
                self.channel_limits.pop(channel.id)
            except discord.Forbidden:
                pass
            except KeyError:
                pass

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        if member.guild.id == ELMO_GUILD_ID:
            if before.channel:
                await self.handle_channel(before.channel)
            if after.channel:
                await self.handle_channel(after.channel)


async def setup(bot: LoobiBot):
    await bot.add_cog(RemoveChannelLimit(bot), guild=discord.Object(ELMO_GUILD_ID))

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
            limit = channel.user_limit
            await channel.edit(user_limit=0)
            self.channel_limits[channel.id] = limit

        # check if the channel limit has returned to normal
        if (
            channel.id in self.channel_limits
            and self.get_human_members(channel) <= self.channel_limits[channel.id]
        ):
            await channel.edit(user_limit=self.channel_limits[channel.id])
            self.channel_limits.pop(channel.id)

    @commands.Cog.listener()
    async def on_voice_state_update(
        self, member, before: discord.VoiceState, after: discord.VoiceState
    ):
        if before.channel:
            await self.handle_channel(before.channel)
        if after.channel:
            await self.handle_channel(after.channel)


async def setup(bot: LoobiBot):
    await bot.add_cog(RemoveChannelLimit(bot), guild=discord.Object(ELMO_GUILD_ID))

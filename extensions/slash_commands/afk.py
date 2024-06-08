from main import *


class AfkCommand(commands.Cog):
    def __init__(self, bot: LoobiBot):
        self.bot = bot

    @app_commands.command(
        name="afk", description="Get voice points for being afk in a voice channel"
    )
    async def afk_command(self, interaction: discord.Interaction):
        # self connection check
        channel = self.bot.get_channel(AFK_CHANNEL_ID)
        if is_connected(self.bot, channel):
            await interaction.response.send_message(
                f"I'm already connected to {channel.name}", ephemeral=True
            )
            return

        # user connection check
        if interaction.user not in channel.members:
            await interaction.response.send_message(
                f"You have to be connected to {channel.mention} to use this command",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)
        try:
            await channel.connect()
            await interaction.edit_original_response(
                content=f"Successfully connected to {channel.name}"
            )
        except Exception as e:
            await interaction.edit_original_response(
                content=f"There was a problem trying to connect to {channel.name}"
            )
            raise e

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        # disconnect from afk channel if it's empty
        channel = self.bot.get_channel(AFK_CHANNEL_ID)
        voice_client: discord.VoiceClient = discord.utils.get(
            self.bot.voice_clients, guild=self.bot.get_guild(GUILD_ID)
        )
        if voice_client is not None and len(channel.members) == 1:
            await voice_client.disconnect(force=True)


async def setup(bot: LoobiBot):
    await bot.add_cog(AfkCommand(bot), guild=discord.Object(GUILD_ID))

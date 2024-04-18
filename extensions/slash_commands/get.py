import aiohttp
import base64
import io
from main import *

"""
from pydub import AudioSegment
class ConvertToMp3View(discord.ui.View):
    def __init__(self, sound: discord.SoundboardSound):
        super().__init__(timeout=TIMEOUT)
        self.sound = sound

    @discord.ui.button(label="Convert to .mp3", style=discord.ButtonStyle.green)
    async def convert_to_mp3(self, interaction: discord.Interaction, button):
        sound_file = io.BytesIO(await self.sound.read())
        sound_file.seek(0)
        audio_data: AudioSegment = AudioSegment.from_file(sound_file)
        mp3_output = io.BytesIO()
        audio_data.export(mp3_output, format="mp3")
        mp3_output.seek(0)
        await interaction.response.edit_message(
            attachments=[discord.File(mp3_output, self.sound.name + ".mp3")], view=None
        )
"""


@app_commands.user_install()
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
class GetCommand(
    commands.GroupCog,
    name="get",
    description="Some getters I made",
):
    def __init__(self, bot: LoobiBot):
        self.bot = bot
        self.mc_api_url = "https://api.mcsrvstat.us/3"
        self.online_color = 0x00FF00
        self.offline_color = 0xFF0000

    @app_commands.command(
        name="server-icon",
        description="Get the icon for this server or group chat, if it exists",
    )
    async def get_server_icon(self, interaction: discord.Interaction):
        # channel check
        if is_in_dm(interaction):
            await interaction.response.send_message(
                "You must use this command inside a server or a group chat",
                ephemeral=True,
            )
            return

        icon = (
            interaction.channel.icon
            if is_in_gc(interaction)
            else interaction.guild.icon
        )
        if icon is None:
            scope = "group chat" if is_in_gc(interaction) else "server"
            await interaction.response.send_message(
                f"This {scope} has no icon", ephemeral=True
            )
        else:
            await interaction.response.send_message(icon.url, ephemeral=True)

    async def emoji_conventer(self, ctx: commands.Context, argument: str):
        try:
            emoji = await commands.EmojiConverter().convert(ctx, argument)
        except commands.EmojiNotFound:
            emoji = discord.utils.get(ctx.guild.emojis, name=argument)
        return emoji

    async def emoji_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ):
        if not is_in_guild(interaction):
            return []

        guessed_emoji = await self.emoji_conventer(
            await self.bot.get_context(interaction), current.rstrip()
        )
        if guessed_emoji is None:
            choices = [
                app_commands.Choice(name=emoji.name, value=str(emoji))
                for emoji in interaction.guild.emojis
                if current.lower() in emoji.name.lower()
            ]
            return choices if len(choices) <= 25 else []
        else:
            return [
                app_commands.Choice(name=guessed_emoji.name, value=str(guessed_emoji))
            ]

    @app_commands.command(
        name="server-emoji", description="Get an emoji from this server"
    )
    @app_commands.describe(name="The name of the emoji")
    @app_commands.autocomplete(name=emoji_autocomplete)
    async def get_server_emoji(self, interaction: discord.Interaction, name: str):
        # channel check
        if not is_in_guild(interaction):
            await must_use_in_guild(interaction)
            return

        emoji = await self.emoji_conventer(
            await self.bot.get_context(interaction), name
        )
        if emoji is None:
            await interaction.response.send_message(
                "Can't find an emoji with that name", ephemeral=True
            )
        else:
            await interaction.response.send_message(emoji.url, ephemeral=True)

    @app_commands.command(
        name="mc-server", description="Get the status of a Minecraft server"
    )
    @app_commands.describe(ip="The IP of the server")
    async def get_mc_server(self, interaction: discord.Interaction, ip: str):
        await interaction.response.defer(ephemeral=True)
        # get server status using the API
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.mc_api_url}/{ip}") as response:
                if response.status == 200:
                    server_status = await response.json()
                else:
                    await interaction.edit_original_response(
                        content="There was a problem fetching the server"
                    )
                    return

        if server_status["online"]:
            embed = discord.Embed(
                color=self.online_color,
                title=server_status["ip"],
                description="\n".join(server_status["motd"]["clean"]),
            )
            embed.set_author(name=ip)
            embed.add_field(
                name="Online",
                value=f"Players: {server_status['players']['online']}/{server_status['players']['max']}",
            )
            embed.set_footer(text=server_status["version"])
            if "icon" in server_status:
                base64_image = server_status["icon"]
                # Remove the data URI prefix
                base64_data = base64_image.split(",")[1]
                # Decode the base64 data
                decoded_image = base64.b64decode(base64_data)
                icon_file = discord.File(
                    io.BytesIO(decoded_image),
                    "server_icon.png",
                )
            else:
                icon_file = discord.File(
                    in_folder(os.path.join("assets", "default_server_icon.png")),
                    "server_icon.png",
                )
            embed.set_thumbnail(url="attachment://server_icon.png")
            await interaction.edit_original_response(
                embed=embed, attachments=[icon_file]
            )
        else:  # server is offline
            embed = discord.Embed(
                color=self.offline_color, title=ip, description="Offline"
            )
            await interaction.edit_original_response(embed=embed)

    def sound_to_str(self, sound: discord.SoundboardSound):
        if sound.emoji is not None and not sound.emoji.is_custom_emoji():
            return str(sound.emoji) + " " + sound.name
        return sound.name

    async def sound_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ):
        if not is_in_guild(interaction):
            return []

        choices = [
            app_commands.Choice(
                name=self.sound_to_str(sound), value=self.sound_to_str(sound)
            )
            for sound in interaction.guild.soundboard_sounds
            if current.lower() in self.sound_to_str(sound)
        ]
        return choices if len(choices) <= 25 else []

    @app_commands.command(
        name="sound", description="Get a sound from this server's soundboard"
    )
    @app_commands.describe(sound="The name of the sound")
    @app_commands.autocomplete(sound=sound_autocomplete)
    async def get_sound(self, interaction: discord.Interaction, sound: str):
        # channel check
        if not is_in_guild(interaction):
            await must_use_in_guild(interaction)
            return

        for soundboard_sound in interaction.guild.soundboard_sounds:
            if self.sound_to_str(soundboard_sound) == sound:
                await interaction.response.send_message(
                    soundboard_sound.url,
                    ephemeral=True,
                )
                return

        await interaction.response.send_message(
            "Can't find a sound with that name", ephemeral=True
        )

    @app_commands.command(name="me", description="See your user/member anywhere")
    async def get_me(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            interaction.user.mention, ephemeral=True
        )


async def setup(bot: LoobiBot):
    await bot.add_cog(GetCommand(bot))

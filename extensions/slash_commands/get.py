import asyncio
import base64
import io
from socket import gaierror
from mcstatus import BedrockServer, JavaServer
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
        self.java_port = 25565
        self.bedrock_port = 19132

    def address_to_str(self, ip: str, port: int):
        if port == self.java_port or port == self.bedrock_port or port == 0:
            return ip
        return f"{ip}:{port}"

    def get_port(self, server_type: str):
        if server_type == "Java":
            return self.java_port
        if server_type == "Bedrock":
            return self.bedrock_port
        return 0

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
            await self.bot.get_context(interaction), current
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
    @app_commands.choices(
        server_type=[
            app_commands.Choice(name="Java", value="Java"),
            app_commands.Choice(name="Bedrock", value="Bedrock"),
        ]
    )
    @app_commands.describe(
        ip="The IP of the server",
        server_type="Java or Bedrock server, leave empty to try both",
    )
    @app_commands.rename(server_type="type")
    async def get_mc_server(
        self, interaction: discord.Interaction, ip: str, server_type: str = "both"
    ):
        # check if there is a port
        if ":" in ip:
            splitted_ip = ip.split(":")
            if len(splitted_ip) == 2 and splitted_ip[1].isdigit():
                ip = splitted_ip[0]
                port = int(splitted_ip[1])
            else:
                await interaction.response.send_message(
                    content="Invalid Address syntax", ephemeral=True
                )
                return
        else:
            port = self.get_port(server_type)

        await interaction.response.defer(ephemeral=True)
        try:
            if server_type == "Java":
                status = await JavaServer(ip, port).async_status()
            elif server_type == "Bedrock":
                status = await BedrockServer(ip, port).async_status()
            elif server_type == "both":
                if port == 0:
                    java = JavaServer(ip, self.java_port).async_status()
                    bedrock = BedrockServer(ip, self.bedrock_port).async_status()
                else:
                    java = JavaServer(ip, port).async_status()
                    bedrock = BedrockServer(ip, port).async_status()
                done, pending = await asyncio.wait(
                    (
                        asyncio.create_task(java, name="Java"),
                        asyncio.create_task(bedrock, name="Bedrock"),
                    ),
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for task in done:
                    exception = task.exception()
                    if exception is not None:
                        raise exception
                    status = task.result()
                    server_type = task.get_name()
                for task in pending:
                    task.cancel()
            else:
                await interaction.edit_original_response(
                    content=f"Invalid server type: {server_type}"
                )
                return
        except ValueError:  # invalid port
            await interaction.edit_original_response(content="Invalid port")
            return
        except gaierror:  # invalid ip address
            await interaction.edit_original_response(content="Invalid Address")
            return
        except Exception as e:
            if (
                isinstance(e, TimeoutError)
                or isinstance(e, ConnectionRefusedError)
                or isinstance(e, OSError)
            ):
                embed = discord.Embed(
                    color=self.offline_color,
                    title=self.address_to_str(ip, port),
                    description="Offline",
                )
                await interaction.edit_original_response(embed=embed)
                return
            await interaction.edit_original_response(
                content=f"Something went wrong when trying to check the status of {self.address_to_str(ip, port)},"
                + f" if this problem continues, please report it to {mention_user(OWNER_ID)}"
            )
            raise e

        embed = discord.Embed(
            color=self.online_color,
            title=self.address_to_str(ip, port),
            description=status.motd.to_plain(),
        )
        embed.set_author(name=f"{server_type} server")
        embed.add_field(
            name="Online",
            value=f"Players: {status.players.online}/{status.players.max}",
        )
        embed.set_footer(text=status.version.name)
        if server_type == "Java":
            if status.icon is not None:
                decoded_image = base64.b64decode(
                    status.icon.removeprefix("data:image/png;base64,")
                )
                icon_file = discord.File(
                    io.BytesIO(decoded_image),
                    "server_icon.png",
                )
            else:
                icon_file = discord.File(
                    in_folder(os.path.join("assets", "default_server_icon.png")),
                    "server_icon.png",
                )
            attachments = [icon_file]
            embed.set_thumbnail(url="attachment://server_icon.png")
        else:
            attachments = []
        await interaction.edit_original_response(embed=embed, attachments=attachments)

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

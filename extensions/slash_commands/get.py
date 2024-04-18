import asyncio
import base64
import io
from socket import gaierror
from mcstatus import BedrockServer, JavaServer
from mcstatus.status_response import BedrockStatusResponse, JavaStatusResponse
from main import *


async def handle_exceptions(
    done: set[asyncio.Task], pending: set[asyncio.Task]
) -> asyncio.Task | None:
    """Handle exceptions from tasks.

    Also, cancel all pending tasks, if found correct one.
    """
    if len(done) == 0:
        raise ValueError("No tasks was given to `done` set.")

    for i, task in enumerate(done):
        if task.exception() is not None:
            if len(pending) == 0:
                continue

            if (
                i == len(done) - 1
            ):  # firstly check all items from `done` set, and then handle pending set
                return await handle_exceptions(
                    *(await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED))
                )
        else:
            for pending_task in pending:
                pending_task.cancel()
            return task


async def handle_java(host: str) -> JavaStatusResponse:
    """A wrapper around mcstatus, to compress it in one function."""
    return await (await JavaServer.async_lookup(host)).async_status()


async def handle_bedrock(host: str) -> BedrockStatusResponse:
    """A wrapper around mcstatus, to compress it in one function."""
    # note: `BedrockServer` doesn't have `async_lookup` method, see it's docstring
    # I added timeout=1 because for some reason it takes 3 times the amount of timeout
    return await BedrockServer.lookup(host, timeout=1).async_status()


@app_commands.user_install()
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
class GetCommand(
    commands.GroupCog,
    name="get",
    description="Some getters I made",
):
    def __init__(self, bot: LoobiBot):
        self.bot = bot
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
        await interaction.response.defer(ephemeral=True)
        try:
            if server_type == "Java":
                status = await handle_java(ip)
            elif server_type == "Bedrock":
                status = await handle_bedrock(ip)
            elif server_type == "both":
                success_task = await handle_exceptions(
                    *(
                        await asyncio.wait(
                            {
                                asyncio.create_task(handle_java(ip), name="Java"),
                                asyncio.create_task(handle_bedrock(ip), name="Bedrock"),
                            },
                            return_when=asyncio.FIRST_COMPLETED,
                        )
                    )
                )
                if success_task is None:
                    raise TimeoutError("No tasks were successful. Is server offline?")
                status = success_task.result()
                server_type = success_task.get_name()
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
                    title=ip,
                    description="Offline",
                )
                await interaction.edit_original_response(embed=embed)
                return
            await interaction.edit_original_response(
                content=f"Something went wrong when trying to check the status of {ip},"
                + f" if this problem continues, please report it to {mention_user(OWNER_ID)}"
            )
            raise e

        embed = discord.Embed(
            color=self.online_color,
            title=ip,
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

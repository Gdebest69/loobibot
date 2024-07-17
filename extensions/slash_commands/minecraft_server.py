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


class MinecraftServerCommand(commands.Cog):
    def __init__(self, bot: LoobiBot):
        self.bot = bot
        self.online_color = 0x00FF00
        self.offline_color = 0xFF0000

    @app_commands.command(
        name="minecraft-server", description="Get the status of a Minecraft server"
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
    @app_commands.user_install()
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
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


async def setup(bot: LoobiBot):
    await bot.add_cog(MinecraftServerCommand(bot))

import urllib3
import asyncio
import base64
import io
from crafty_client import Crafty4, static
from discord.ext import tasks
from main import *


class ButtonOnCooldown(commands.CommandError):
    def __init__(self, retry_after: float):
        self.retry_after = retry_after


class ServerListView(discord.ui.View):
    def __init__(self, cog: "Crafty"):
        super().__init__(timeout=None)
        self.cog = cog
        self.cd: commands.CooldownMapping = commands.CooldownMapping.from_cooldown(
            1, 60, lambda i: 1
        )

    def format_timedelta(self, total_seconds: float):
        now = datetime.datetime.now()
        cooldown_time = now + datetime.timedelta(seconds=total_seconds)
        return discord.utils.format_dt(cooldown_time, "R")

    async def interaction_check(self, interaction: discord.Interaction):
        retry_after = self.cd.update_rate_limit(interaction)
        if retry_after:
            # rate limited
            # we could raise `commands.CommandOnCooldown` instead, but we only need the `retry_after` value
            raise ButtonOnCooldown(retry_after)

        # not rate limited
        return True

    async def on_error(
        self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item
    ):
        if isinstance(error, ButtonOnCooldown):
            await interaction.response.send_message(
                f"You can use this again in {time_remaining(error.retry_after)}",
                ephemeral=True,
            )
        else:
            # call the original on_error, which prints the traceback to stderr
            await super().on_error(interaction, error, item)

    @discord.ui.button(label="Update", style=discord.ButtonStyle.green)
    async def update_button(self, interaction: discord.Interaction, button):
        await interaction.response.defer()
        embeds, attachments = await self.cog.servers_list_embeds()
        await interaction.message.edit(embeds=embeds, attachments=attachments)


class Crafty(commands.Cog):
    def __init__(self, bot: LoobiBot):
        self.bot = bot
        self.crafty = Crafty4(CRAFTY_URL, CRAFTY_TOKEN)
        self.offline_color = 0xFF0000
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self.update_server_list.start()

    async def servers_list_embeds(self):
        servers = await asyncio.to_thread(self.crafty.list_mc_servers)
        ip = await get_router_ip()
        default_embed = discord.Embed(
            title="There are no online servers", color=self.offline_color
        )
        if ip is None:
            return [default_embed], []
        embeds = []
        attachments = []
        default_server_icon = None
        for i, server in enumerate(servers):
            server_stats = await asyncio.to_thread(
                self.crafty.get_server_stats, server["server_id"]
            )
            if server_stats["running"]:
                embed = discord.Embed(
                    title=server_stats["server_id"]["server_name"],
                    description=f"{ip}:{server_stats['server_id']['server_port']}",
                    color=EMBED_COLOR,
                )
                embed.set_author(name=server_stats["server_id"]["type"])
                embed.set_footer(text=server_stats["version"])
                if (
                    server_stats["icon"] != ""
                    and server_stats["icon"] != "False"
                    and server_stats["icon"] is not None
                ):
                    decoded_image = base64.b64decode(server_stats["icon"])
                    icon_file = discord.File(
                        io.BytesIO(decoded_image),
                        f"{i}.png",
                    )
                    embed.set_thumbnail(url=f"attachment://{i}.png")
                    attachments.append(icon_file)
                else:
                    embed.set_thumbnail(url="attachment://default_server_icon.png")
                    if default_server_icon is None:
                        default_server_icon = discord.File(
                            in_folder(
                                os.path.join("assets", "default_server_icon.png")
                            ),
                            "default_server_icon.png",
                        )
                        attachments.append(default_server_icon)
                embeds.append(embed)

        return (embeds, attachments) if embeds else ([default_embed], [])

    async def server_list_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ):

        servers = await asyncio.to_thread(self.crafty.list_mc_servers)
        choices = [
            app_commands.Choice(name=server["server_name"], value=server["server_id"])
            for server in servers
            if current.lower() in server["server_name"].lower()
            and server["type"] == "minecraft-java"
        ]
        return choices if len(choices) <= 25 else []

    @app_commands.command(
        name="server-list",
        description="Send a new message in this channel which will show all the servers hosted in crafty controller",
    )
    @app_commands.default_permissions()
    async def server_list_command(self, interaction: discord.Interaction):
        # permission check
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "You must have administrator permissions to use this command",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)
        try:
            embeds, attachments = await self.servers_list_embeds()
            message = await interaction.channel.send(
                embeds=embeds, files=attachments, view=ServerListView(self)
            )
            self.bot.server_list_message = (message.channel.id, message.id)
            await interaction.edit_original_response(
                content="Successfully sent a new server list message"
            )
        except Exception as e:
            if isinstance(e, discord.Forbidden):
                await interaction.edit_original_response(
                    content="Sorry, but I can't send a message in this channel due to lack of permissions in this server",
                )
            else:
                await interaction.edit_original_response(
                    content="Something went wrong when trying to send a message in this channel,"
                    + f" if this problem continues, please report it to {mention_user(OWNER_ID)}",
                )
                raise e

    @app_commands.command(
        name="whitelist",
        description="Add any player to a whitelist in any of the servers hosted in crafty controller",
    )
    @app_commands.autocomplete(server=server_list_autocomplete)
    @app_commands.describe(
        server="The server to add the player to", username="The Minecraft username"
    )
    async def whitelist_command(
        self, interaction: discord.Interaction, server: str, username: str
    ):
        try:
            r = await asyncio.to_thread(
                self.crafty.run_command, server, f"whitelist add {username}"
            )
            if r is None:
                await interaction.response.send_message(
                    "Server is offline", ephemeral=True
                )
                return
            if not r:  # r = {} which means it worked
                await interaction.response.send_message(
                    "Successfully sent whitelist command", ephemeral=True
                )
        except static.exceptions.AccessDenied:
            await interaction.response.send_message("Server not found", ephemeral=True)

    @tasks.loop(hours=1)
    async def update_server_list(self):
        channel_id, message_id = self.bot.server_list_message
        try:
            message = await self.bot.get_channel(channel_id).fetch_message(message_id)
        except discord.NotFound:
            message = None
        if message is not None:
            embeds, attachments = await self.servers_list_embeds()
            await message.edit(embeds=embeds, attachments=attachments)


async def update_view(cog: Crafty):
    channel_id, message_id = cog.bot.server_list_message
    try:
        message = await cog.bot.get_channel(channel_id).fetch_message(message_id)
    except discord.NotFound:
        message = None
    if message is not None:
        await message.edit(view=ServerListView(cog))


async def setup(bot: LoobiBot):
    cog = Crafty(bot)
    await bot.add_cog(cog, guild=discord.Object(GUILD_ID))
    asyncio.create_task(update_view(cog))

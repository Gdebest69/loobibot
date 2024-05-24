import urllib3
import asyncio
from crafty_client import Crafty4
from main import *


class Crafty(commands.Cog):
    def __init__(self, bot: LoobiBot):
        self.bot = bot
        self.crafty = Crafty4(CRAFTY_URL, CRAFTY_TOKEN)
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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

        servers = await asyncio.to_thread(self.crafty.list_mc_servers)


async def setup(bot: LoobiBot):
    await bot.add_cog(Crafty(bot), guild=discord.Object(GUILD_ID))

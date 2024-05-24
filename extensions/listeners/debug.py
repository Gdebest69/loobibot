import aiohttp
import subprocess
from wakeonlan import send_magic_packet
from main import *


class DebugCommands(commands.Cog):
    def __init__(self, bot: LoobiBot):
        self.bot = bot
        # WOL
        self.mac_address = "08:bf:b8:31:41:1e"
        self.ip_address = "10.100.102.27"
        self.devices = {
            "my_pc": {"mac": self.mac_address, "ip_address": self.ip_address}
        }

    def wake_device(self, device_name):
        if device_name in self.devices:
            mac, ip = self.devices[device_name].values()
            send_magic_packet(mac, ip_address=ip)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        # debug
        if message.author.id == OWNER_ID:
            # toggle vacation mode
            if message.content == "/toggle vacation":
                self.bot.vacation = not self.bot.vacation
                await message.reply(
                    f"Vacation mode is now set to {self.bot.vacation}",
                    mention_author=False,
                )

            # shut down bot
            if message.content == "/shutdown":
                self.bot.save_data()
                await message.add_reaction(
                    self.bot.get_guild(GUILD_ID).get_emoji(770191069198811156)
                )
                await self.bot.close()

            # update bot
            if message.content == "/update":
                paused_message = await message.reply(
                    "Updating bot...", mention_author=False
                )
                self.bot.save_data()
                try:
                    subprocess.run(["git", "pull"])
                except Exception as e:
                    await message.channel.send(
                        f"Error occurred while executing git pull: {e}"
                    )
                    raise e
                os.execl(
                    sys.executable,
                    sys.executable,
                    in_folder("main.py"),
                    str(message.channel.id),
                    str(paused_message.id),
                )

            # pause bot
            if message.content == "/pause":
                paused_message = await message.reply(
                    "Pausing bot...", mention_author=False
                )
                self.bot.save_data()
                os.execl(
                    sys.executable,
                    sys.executable,
                    in_folder("paused.py"),
                    str(message.channel.id),
                    str(paused_message.id),
                )

            # sync commands
            if message.content == "/sync":
                await self.bot.tree.sync(guild=discord.Object(GUILD_ID))
                await self.bot.tree.sync(guild=discord.Object(TEST_GUILD_ID))
                await self.bot.tree.sync()
                await message.reply("Successfully synced")

            # ip command
            if message.content == "/ip":
                ip = await get_router_ip()
                if ip is None:
                    await message.reply("There was an error", mention_author=False)
                    return
                await message.reply(ip, mention_author=False)

            # WOL command
            if message.content == "/wol":
                self.wake_device("my_pc")
                await message.reply("Successfully woke up the PC", mention_author=False)


async def setup(bot: LoobiBot):
    await bot.add_cog(DebugCommands(bot))


"""
if message.author.id == OWNER_ID and message.content == "/embed":
    GREEN = 0x00ff00
    embed = discord.Embed(color=GREEN, title="title", url="https://www.google.com/", description="description",
                          timestamp=datetime.datetime.now())
    embed.set_image(url="https://www.simplilearn.com/ice9/free_resources_article_thumb/what_is_image_Processing.jpg")
    embed.set_author(name="author name", url="https://developer.wordpress.org/reference/functions/the_author_url/",
                     icon_url="https://cdn-icons-png.flaticon.com/512/1078/1078454.png")
    embed.set_thumbnail(url="https://i.ytimg.com/vi/vx5dSS3BBOk/maxresdefault.jpg")
    embed.set_footer(text="footer text", icon_url="https://blog.hubspot.com/hs-fs/hubfs/Tenzo%20Tea.png?width=650&name=Tenzo%20Tea.png")
    embed.add_field(name="name 1", value="value 1", inline=False)
    embed.add_field(name="name 2", value="value 2", inline=False)
    embed.add_field(name="name 3", value="value 3", inline=True)
    embed.add_field(name="name 4", value="value 4", inline=True)
    await message.reply(embed=embed, mention_author=False)
"""

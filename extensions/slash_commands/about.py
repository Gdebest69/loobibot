import subprocess
from main import *


class AboutCommand(commands.Cog):
    def __init__(self, bot: LoobiBot):
        self.bot = bot
        self.version_info = self.get_version_info()

    def get_version_info(self):
        def run(cmd):
            try:
                return (
                    subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
                    .decode("utf-8")
                    .strip()
                )
            except Exception as e:
                self.bot.logger.warning(f"Failed to run command {cmd}: {e}")
                return None

        # Python version
        python_version_info = sys.version_info
        python_version = f"Python v{python_version_info.major}.{python_version_info.minor}.{python_version_info.micro}"

        # Discord.py version
        discord_version_info = discord.version_info
        discord_version = f"discord.py v{discord_version_info.major}.{discord_version_info.minor}.{discord_version_info.micro} {discord_version_info.releaselevel}"

        # loobi bot version
        commit_hash = run(["git", "rev-parse", "HEAD"])
        if commit_hash is None:
            commit_hash = "Unavailable"
        publish_date = run(["git", "log", "-1", "--format=%cd", "--date=iso-strict"])
        if publish_date is None:
            publish_date = "Unavailable"
        else:
            publish_date = discord.utils.format_dt(
                datetime.datetime.fromisoformat(publish_date), style="f"
            )

        loobi_bot_version = (
            f"Current commit hash: `{commit_hash}`\nPublished on: {publish_date}"
        )
        if self.bot.testing:
            loobi_bot_version += "\n**The bot is in testing mode**"

        return {
            "Python version": python_version,
            "discord.py version": discord_version,
            "loobi bot version": loobi_bot_version,
        }

    @app_commands.command(name="about", description="Get information about the bot")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def about(self, interaction: discord.Interaction):
        embed = discord.Embed(
            color=EMBED_COLOR,
            title="About loobi bot",
            description=f"Owner: {mention_user(OWNER_ID)}",
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        for key, value in self.version_info.items():
            embed.add_field(name=key, value=value, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: LoobiBot):
    await bot.add_cog(AboutCommand(bot))

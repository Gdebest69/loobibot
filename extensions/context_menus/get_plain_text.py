import asyncio
from io import StringIO
from main import *


class GetPlainTextCommand(commands.Cog):
    def __init__(self, bot: LoobiBot):
        self.bot = bot
        self.get_plain_text_ctx_menu = app_commands.ContextMenu(
            name="Get Plain Text",
            callback=self.get_plain_text,
        )
        self.bot.tree.add_command(self.get_plain_text_ctx_menu)

    @app_commands.user_install()
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def get_plain_text(
        self, interaction: discord.Interaction, message: discord.Message
    ):
        if len(message.content) == 0:
            await interaction.response.send_message(
                "Message content is empty", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                file=discord.File(StringIO(message.content), filename="message.txt"),
                ephemeral=True,
            )


async def setup(bot: LoobiBot):
    await bot.add_cog(GetPlainTextCommand(bot))

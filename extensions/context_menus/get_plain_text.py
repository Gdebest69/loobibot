import json
from io import StringIO
from main import *


class LastEmbedView(discord.ui.View):
    def __init__(self, last_embed: discord.Embed):
        super().__init__(timeout=TIMEOUT)
        self.embed = last_embed
        self.message: discord.Message = None

    @discord.ui.button(label="View last embed", style=discord.ButtonStyle.green)
    async def send_last_embed(self, interaction: discord.Interaction, button):
        await interaction.response.send_message(
            file=discord.File(
                StringIO(json.dumps(self.embed.to_dict(), indent=4)),
                filename="embed9.json",
            ),
            ephemeral=True,
        )

    async def on_timeout(self):
        if self.message is not None:
            await self.message.edit(view=None)


class GetPlainTextCommand(commands.Cog):
    def __init__(self, bot: LoobiBot):
        self.bot = bot
        self.get_plain_text_ctx_menu = app_commands.ContextMenu(
            name="Get plain text",
            callback=self.get_plain_text,
        )
        self.bot.tree.add_command(self.get_plain_text_ctx_menu)

    @app_commands.user_install()
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def get_plain_text(
        self, interaction: discord.Interaction, message: discord.Message
    ):
        embed_files = [
            discord.File(
                StringIO(json.dumps(embed.to_dict(), indent=4)),
                filename=f"embed{i}.json",
            )
            for i, embed in enumerate(message.embeds)
        ]
        files = (
            [discord.File(StringIO(message.content), filename="message.txt")]
            if len(message.content) > 0
            else []
        ) + embed_files
        if len(files) == 0:
            await interaction.response.send_message(
                "Message content is empty", ephemeral=True
            )
        elif len(files) <= 10:
            await interaction.response.send_message(files=files, ephemeral=True)
        else:
            view = LastEmbedView(message.embeds[9])
            await interaction.response.send_message(
                files=files[:10],
                ephemeral=True,
                view=view,
            )
            view.message = await interaction.original_response()


async def setup(bot: LoobiBot):
    await bot.add_cog(GetPlainTextCommand(bot))

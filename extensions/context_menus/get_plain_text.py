import json
from io import StringIO
from asyncio import create_task
from main import *


class LastEmbedView(discord.ui.View):
    def __init__(self, last_embed: discord.Embed, original_message: discord.Message):
        super().__init__(timeout=TIMEOUT)
        self.embed = last_embed
        self.original_message = original_message
        self.message: discord.Message = None

    @discord.ui.button(label="View last embed", style=discord.ButtonStyle.green)
    async def send_last_embed(self, interaction: discord.Interaction, button):
        await interaction.response.send_message(
            file=discord.File(
                StringIO(json.dumps(self.embed.to_dict(), indent=4)),
                filename=f"embed9_{self.original_message.id}.json",
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
        thinking_task = create_task(interaction.response.defer(ephemeral=True))
        embed_files = [
            discord.File(
                StringIO(json.dumps(embed.to_dict(), indent=4)),
                filename=f"embed{i}_{message.id}.json",
            )
            for i, embed in enumerate(message.embeds)
        ]
        files = (
            [
                discord.File(
                    StringIO(message.content), filename=f"message_{message.id}.txt"
                )
            ]
            if len(message.content) > 0
            else []
        ) + embed_files

        if message.stickers:
            sticker_list_message = "\n".join(
                [sticker.url for sticker in message.stickers]
            )
        else:
            sticker_list_message = None

        await thinking_task
        if len(files) == 0:
            if sticker_list_message is None:
                await interaction.edit_original_response(
                    content="Message content is empty"
                )
            else:
                await interaction.edit_original_response(content=sticker_list_message)
        elif len(files) <= 10:
            await interaction.edit_original_response(
                content=sticker_list_message, attachments=files
            )
        else:
            view = LastEmbedView(message.embeds[9], message)
            await interaction.edit_original_response(
                content=sticker_list_message, attachments=files[:10], view=view
            )
            view.message = await interaction.original_response()


async def setup(bot: LoobiBot):
    await bot.add_cog(GetPlainTextCommand(bot))

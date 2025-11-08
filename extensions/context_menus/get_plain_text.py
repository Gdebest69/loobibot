import json
from io import StringIO, BytesIO
from asyncio import create_task
from zipfile import ZipFile
from main import *


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
        component_files = [
            discord.File(
                StringIO(json.dumps(component.to_dict(), indent=4)),
                filename=f"component{i}_{message.id}.json",
            )
            for i, component in enumerate(message.components)
        ]
        files = []
        if message.content:
            files.append(
                discord.File(
                    StringIO(message.content), filename=f"message_{message.id}.txt"
                )
            )
        files += embed_files
        files += component_files

        if message.stickers:
            sticker_list_message = "\n".join(
                [sticker.url for sticker in message.stickers]
            )
        else:
            sticker_list_message = None

        await thinking_task
        if not files and sticker_list_message is None:
            await interaction.edit_original_response(content="Message content is empty")
        elif len(files) <= 10:
            await interaction.edit_original_response(
                content=sticker_list_message, attachments=files
            )
        else:
            # Create a zip file with all the files beacause discord only allows 10 attachments per message
            zip_buffer = BytesIO()
            with ZipFile(zip_buffer, "x") as zip_file:
                for discord_file in files:
                    zip_file.writestr(discord_file.filename, discord_file.fp.read())
            zip_buffer.seek(0)
            zip_file = discord.File(zip_buffer, filename=f"{message.id}.zip")
            await interaction.edit_original_response(
                content=sticker_list_message, attachments=[zip_file]
            )


async def setup(bot: LoobiBot):
    await bot.add_cog(GetPlainTextCommand(bot))

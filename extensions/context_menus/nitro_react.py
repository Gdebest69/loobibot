from discord.ui import Modal, TextInput
from discord.utils import MISSING
from main import *


class EmojiModal(Modal):
    emoji_name = TextInput(label="Emoji name", placeholder="The name of the emoji")
    emoji_id = TextInput(label="Emoji id", placeholder="The id of the emoji")

    def __init__(self, message: discord.Message) -> None:
        super().__init__(title="Add the emoji data", timeout=None)
        self.message = message

    async def on_submit(self, interaction: discord.Interaction):
        # data check
        if not self.emoji_id.value.isdigit():
            await interaction.response.send_message(
                "The id must be a positive integer", ephemeral=True
            )
            return
        emoji_str = f"{self.emoji_name}:{self.emoji_id}"
        try:
            await self.message._state.http.add_reaction(
                self.message.channel.id, self.message.id, emoji_str
            )
            await interaction.response.defer()
        except discord.errors.Forbidden:
            await interaction.response.send_message(
                "Sorry, but I can't react to the message due to lack of permissions in this server",
                ephemeral=True,
            )
        except discord.errors.HTTPException:
            await interaction.response.send_message("Unknown emoji", ephemeral=True)


class NitroReactCommand(commands.Cog):
    def __init__(self, bot: LoobiBot):
        self.bot = bot
        self.nitro_react_ctx_menu = app_commands.ContextMenu(
            name="Nitro React", callback=self.nitro_react
        )
        self.bot.tree.add_command(self.nitro_react_ctx_menu)

    async def nitro_react(
        self, interaction: discord.Interaction, message: discord.Message
    ):
        await interaction.response.send_modal(EmojiModal(message))


async def setup(bot: LoobiBot):
    await bot.add_cog(NitroReactCommand(bot))

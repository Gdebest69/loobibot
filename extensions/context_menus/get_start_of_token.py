import base64
from main import *


class GetStartOfTokenCommand(commands.Cog):
    def __init__(self, bot: LoobiBot):
        self.bot = bot
        self.get_start_of_token_ctx_menu = app_commands.ContextMenu(
            name="Get start of token", callback=self.get_start_of_token
        )
        self.bot.tree.add_command(self.get_start_of_token_ctx_menu)

    @app_commands.user_install()
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def get_start_of_token(
        self, interaction: discord.Interaction, user: discord.Member
    ):
        start_of_token = self.string_to_base64(str(user.id))
        view = discord.ui.View(timeout=1)
        explanation_button = discord.ui.Button(
            label="How does it work?",
            url="https://github.com/Discord-Oxygen/Discord-Console-hacks/issues/2",
            emoji="🤔",
        )
        view.add_item(explanation_button)
        await interaction.response.send_message(
            f"`{start_of_token}`", view=view, ephemeral=True
        )

    def string_to_base64(self, input_string: str):
        # Convert the input string to bytes
        input_bytes = input_string.encode("utf-8")
        # Encode the bytes to base64
        base64_encoded = base64.b64encode(input_bytes)
        # Remove trailing equal signs
        base64_encoded_string = base64_encoded.rstrip(b"=").decode("utf-8")
        return base64_encoded_string


async def setup(bot: LoobiBot):
    await bot.add_cog(GetStartOfTokenCommand(bot))

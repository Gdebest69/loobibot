from discord.ui import Modal, TextInput
from main import *


class EmojiModal(Modal):
    emoji_name = TextInput(
        label="Emoji name",
        placeholder="The name of the emoji",
        min_length=1,
        max_length=100,
    )
    emoji_id = TextInput(
        label="Emoji id",
        placeholder="The id of the emoji",
        min_length=1,
        max_length=100,
    )

    def __init__(self, message: discord.Message) -> None:
        super().__init__(
            title="The emoji must be in a server which I'm in", timeout=None
        )
        self.message = message

    async def on_submit(self, interaction: discord.Interaction):
        # data check
        if not self.emoji_id.value.isdigit():
            await interaction.response.send_message(
                "The id must be a positive integer", ephemeral=True
            )
            return

        emoji = discord.PartialEmoji.from_str(f"{self.emoji_name}:{self.emoji_id}")
        try:
            await self.message.add_reaction(emoji)
            await interaction.response.defer()
        except discord.errors.Forbidden:
            await interaction.response.send_message(
                "Sorry, but I can't react to the message due to lack of permissions in this server",
                ephemeral=True,
            )
        except discord.errors.HTTPException:
            await interaction.response.send_message("Unknown emoji", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(
                "Something went wrong when trying to react to the message,"
                + f" if this problem continues, please report it to {mention_user(OWNER_ID)}",
                ephemeral=True,
            )
            raise e


class NitroReactCommand(commands.Cog):
    def __init__(self, bot: LoobiBot):
        self.bot = bot
        self.nitro_react_ctx_menu = app_commands.ContextMenu(
            name="Nitro react",
            callback=self.nitro_react,
            allowed_installs=app_commands.AppInstallationType(guild=True, user=False),
        )
        self.bot.tree.add_command(self.nitro_react_ctx_menu)

    @app_commands.default_permissions()
    async def nitro_react(
        self, interaction: discord.Interaction, message: discord.Message
    ):
        if (
            is_in_guild(interaction)
            and not interaction.user.guild_permissions.administrator
        ):
            await interaction.response.send_message(
                "You must have administrator permissions to use this", ephemeral=True
            )
            return

        await interaction.response.send_modal(EmojiModal(message))


async def setup(bot: LoobiBot):
    await bot.add_cog(NitroReactCommand(bot))

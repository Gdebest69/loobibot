from main import *


class GetReactedEmojisCommand(commands.Cog):
    def __init__(self, bot: LoobiBot):
        self.bot = bot
        self.get_reacted_emojis_ctx_menu = app_commands.ContextMenu(
            name="Get reacted emojis",
            callback=self.get_reacted_emojis,
        )
        self.bot.tree.add_command(self.get_reacted_emojis_ctx_menu)

    @app_commands.allowed_installs(guilds=False, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def get_reacted_emojis(
        self, interaction: discord.Interaction, message: discord.Message
    ):
        emojis = []
        for reaction in message.reactions:
            if isinstance(reaction.emoji, discord.PartialEmoji) or isinstance(
                reaction.emoji, discord.Emoji
            ):
                emojis.append(
                    f"{reaction.emoji.url} name: `{reaction.emoji.name}` id: `{reaction.emoji.id}`"
                )
            elif isinstance(reaction.emoji, str):
                emoji_url, emoji_name = get_emoji_asset(reaction.emoji)
                if emoji_url is not None:
                    emojis.append(f"{emoji_url} name: `{emoji_name}`")
        if emojis:
            await interaction.response.send_message("\n".join(emojis), ephemeral=True)
        else:
            await interaction.response.send_message(
                "No emojis were reacted to this message", ephemeral=True
            )


async def setup(bot: LoobiBot):
    await bot.add_cog(GetReactedEmojisCommand(bot))

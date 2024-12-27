from main import *


class GetEmojiCommand(commands.Cog):
    def __init__(self, bot: LoobiBot):
        self.bot = bot

    @app_commands.command(
        name="get-emoji",
        description="Get an emoji from any server by choosing it from the emojis menu",
    )
    @app_commands.describe(emoji_str="The selected emoji")
    @app_commands.rename(emoji_str="emoji")
    @app_commands.user_install()
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def get_emoji_command(self, interaction: discord.Interaction, emoji_str: str):
        ctx = await self.bot.get_context(interaction)
        try:
            emoji = await commands.PartialEmojiConverter().convert(ctx, emoji_str)
            await interaction.response.send_message(
                f"{emoji.url}\nname: `{emoji.name}`\nid: `{emoji.id}`", ephemeral=True
            )
        except commands.PartialEmojiConversionFailure:
            await interaction.response.send_message(
                "Couldn't convert your input to an emoji", ephemeral=True
            )


async def setup(bot: LoobiBot):
    await bot.add_cog(GetEmojiCommand(bot))

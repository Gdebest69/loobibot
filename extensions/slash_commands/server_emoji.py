from main import *


class ServerEmojiCommand(commands.Cog):
    def __init__(self, bot: LoobiBot):
        self.bot = bot

    async def emoji_conventer(self, ctx: commands.Context, argument: str):
        try:
            emoji = await commands.PartialEmojiConverter().convert(ctx, argument)
        except commands.PartialEmojiConversionFailure:
            emoji = discord.utils.get(ctx.guild.emojis, name=argument)
        return emoji

    async def emoji_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ):
        if not is_in_guild(interaction):
            return []

        guessed_emoji = await self.emoji_conventer(
            await self.bot.get_context(interaction), current.rstrip()
        )
        if guessed_emoji is None:
            choices = [
                app_commands.Choice(name=emoji.name, value=str(emoji))
                for emoji in interaction.guild.emojis
                if current.lower() in emoji.name.lower()
            ]
            return choices if len(choices) <= 25 else []
        else:
            return [
                app_commands.Choice(name=guessed_emoji.name, value=str(guessed_emoji))
            ]

    @app_commands.command(
        name="server-emoji", description="Get an emoji from this server"
    )
    @app_commands.guild_only()
    @app_commands.allowed_installs(guilds=True, users=False)
    @app_commands.describe(name="The name of the emoji")
    @app_commands.autocomplete(name=emoji_autocomplete)
    async def get_server_emoji(self, interaction: discord.Interaction, name: str):
        # channel check
        if not is_in_guild(interaction):
            await must_use_in_guild(interaction)
            return

        emoji = await self.emoji_conventer(
            await self.bot.get_context(interaction), name
        )
        if emoji is None:
            await interaction.response.send_message(
                "Can't find an emoji with that name", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"{emoji.url}\nname: `{emoji.name}`\nid: `{emoji.id}`", ephemeral=True
            )


async def setup(bot: LoobiBot):
    await bot.add_cog(ServerEmojiCommand(bot))

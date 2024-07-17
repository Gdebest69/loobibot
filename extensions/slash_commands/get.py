from main import *


@app_commands.guild_only()
class GetCommand(
    commands.GroupCog,
    name="get",
    description="Some getters I made",
):
    def __init__(self, bot: LoobiBot):
        self.bot = bot

    @app_commands.command(
        name="server-icon",
        description="Get the icon for this server, if it exists",
    )
    async def get_server_icon(self, interaction: discord.Interaction):
        # channel check
        if is_in_dm(interaction):
            await interaction.response.send_message(
                "You must use this command inside a server",
                ephemeral=True,
            )
            return

        icon = interaction.guild.icon
        if icon is None:
            await interaction.response.send_message(
                f"This server has no icon", ephemeral=True
            )
        else:
            await interaction.response.send_message(icon.url, ephemeral=True)

    async def emoji_conventer(self, ctx: commands.Context, argument: str):
        try:
            emoji = await commands.EmojiConverter().convert(ctx, argument)
        except commands.EmojiNotFound:
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

    def sound_to_str(self, sound: discord.SoundboardSound):
        if sound.emoji is not None and not sound.emoji.is_custom_emoji():
            return str(sound.emoji) + " " + sound.name
        return sound.name

    async def sound_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ):
        if not is_in_guild(interaction):
            return []

        choices = [
            app_commands.Choice(
                name=self.sound_to_str(sound), value=self.sound_to_str(sound)
            )
            for sound in interaction.guild.soundboard_sounds
            if current.lower() in self.sound_to_str(sound)
        ]
        return choices if len(choices) <= 25 else []

    @app_commands.command(
        name="sound", description="Get a sound from this server's soundboard"
    )
    @app_commands.describe(sound="The name of the sound")
    @app_commands.autocomplete(sound=sound_autocomplete)
    async def get_sound(self, interaction: discord.Interaction, sound: str):
        # channel check
        if not is_in_guild(interaction):
            await must_use_in_guild(interaction)
            return

        for soundboard_sound in interaction.guild.soundboard_sounds:
            if self.sound_to_str(soundboard_sound) == sound:
                await interaction.response.send_message(
                    soundboard_sound.url,
                    ephemeral=True,
                )
                return

        await interaction.response.send_message(
            "Can't find a sound with that name", ephemeral=True
        )

    @app_commands.command(
        name="me", description="Silently mentions you so you can see your roles etc."
    )
    async def get_me(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            interaction.user.mention, ephemeral=True
        )


async def setup(bot: LoobiBot):
    await bot.add_cog(GetCommand(bot))

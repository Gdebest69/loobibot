import discord

from main import *


class NickAllCommand(commands.Cog):
    def __init__(self, bot: LoobiBot):
        self.bot = bot

    @app_commands.command(
        name="nick-all",
        description="Change the nicknames of all members with a specific role",
    )
    @app_commands.describe(
        role="The specific role",
        name="The new nickname. Leave empty to reset the nicknames",
    )
    async def nick_all_command(
        self, interaction: discord.Interaction, role: discord.Role, name: str = ""
    ):
        # roles check
        if not has_one_of_roles(interaction.user, NICK_ALL_ROLES_ID):
            await send_invalid_permission(interaction, NICK_ALL_ROLES_ID)
            return

        # block @everyone
        if role.position == 0:
            await interaction.response.send_message(
                "You can't use that role", ephemeral=True
            )
            return

        members = interaction.guild.members
        upper_role = interaction.user.roles[-1]
        changed_names = []
        await interaction.response.send_message("Changing names...", ephemeral=True)
        for member in members:
            if role in member.roles and upper_role.position > member.roles[-1].position:
                await member.edit(nick=name)
                changed_names.append(member.name)
        if not changed_names:
            await interaction.edit_original_response(
                content="No nickname had been changed"
            )
        else:
            await interaction.edit_original_response(
                content=f"Successfully change the nickname of the following members:\n{', '.join(changed_names)}"
            )


async def setup(bot: LoobiBot):
    await bot.add_cog(NickAllCommand(bot), guild=discord.Object(GUILD_ID))

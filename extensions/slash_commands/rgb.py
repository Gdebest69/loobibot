from main import *


class RgbCommand(commands.Cog):
    def __init__(self, bot: LoobiBot):
        self.bot = bot

    @app_commands.command(name="rgb", description="Toggle rgb effect")
    async def rgb_command(self, interaction: discord.Interaction):
        # roles check
        if not has_one_of_roles(interaction.user, RGB_ROLES_ID):
            await send_invalid_permission(interaction, RGB_ROLES_ID)
            return

        rgb_role = interaction.guild.get_role(RGB_ROLE_ID)
        member = interaction.user
        roles = member.roles
        if rgb_role in roles:
            await member.remove_roles(rgb_role)
            await interaction.response.send_message(
                "Successfully disabled rgb effect", ephemeral=True
            )
        else:
            await member.add_roles(rgb_role)
            await interaction.response.send_message(
                "Successfully enabled rgb effect", ephemeral=True
            )


async def setup(bot: LoobiBot):
    await bot.add_cog(RgbCommand(bot), guild=discord.Object(GUILD_ID))

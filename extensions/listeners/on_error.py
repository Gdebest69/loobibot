import traceback
from main import *


"""@bot.tree.error
async def tree_error_handler(interaction: discord.Interaction, error: app_commands.AppCommandError):
    class ErrorView(discord.ui.View):
        @discord.ui.button(label="Full error", emoji="🤓", style=discord.ButtonStyle.red)
        async def show_full_error(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.edit_message(content=f"```{error_traceback[:1994]}```", view=None)

    error_traceback = traceback.format_exc()
    error_text = f"{time_prefix()} [ERROR   ] discord.app_commands.tree:" \
                 f" Ignoring exception in command '{interaction.command.name}'\n" \
                 f"{error_traceback}"
    error_response = f"There was an error with the interaction 😁\n||{error}||"
    view = ErrorView(timeout=None)
    print(error_text)
    if interaction.response.is_done():
        await interaction.edit_original_response(content=error_response, view=view)
    else:
        await interaction.response.send_message(error_response, view=view, ephemeral=True)"""


async def setup(bot: LoobiBot):
    pass

from main import *


class NitroReactCommand(commands.Cog):
    def __init__(self, bot: LoobiBot):
        self.bot = bot
        self.nitro_react_ctx_menu = app_commands.ContextMenu(
            name="Nitro React", callback=self.nitro_react
        )
        self.bot.tree.add_command(self.nitro_react_ctx_menu)

    async def nitro_react(
        self, interaction: discord.Interaction, message: discord.Message
    ): ...


async def setup(bot: LoobiBot):
    await bot.add_cog(NitroReactCommand(bot))

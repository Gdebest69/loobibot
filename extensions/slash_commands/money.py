from main import *


class MoneyCommand(
    commands.GroupCog,
    name="money",
    description="Commands related to the loobi currency",
):
    def __init__(self, bot: LoobiBot):
        self.bot = bot
        self.get_money_ctx_menu = app_commands.ContextMenu(
            name="Get money", callback=self.get_money
        )
        self.bot.tree.add_command(self.get_money_ctx_menu)

    def format_timedelta(self, total_seconds: float):
        now = datetime.datetime.now()
        cooldown_time = now + datetime.timedelta(seconds=total_seconds)
        return discord.utils.format_dt(cooldown_time, "R")

    @app_commands.command(name="claim", description="Claim 100$ every 24 hours")
    @app_commands.checks.cooldown(
        1,
        86400,
    )
    async def money_claim(self, interaction: discord.Interaction):
        if self.bot.testing:
            await interaction.response.send_message(
                "This command is temporarily disabled", ephemeral=True
            )
            return

        self.bot.get_user_data(interaction.user.id).money += 100
        await interaction.response.send_message(
            "You successfully claimed 100$", ephemeral=True
        )

    @money_claim.error
    async def on_claim_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                f"You can you this again in {time_remaining(error.retry_after)}",
                ephemeral=True,
            )
        else:
            raise error

    @app_commands.command(
        name="get", description="Check how much money does a user have"
    )
    @app_commands.describe(user="The user checked")
    async def money_get(
        self, interaction: discord.Interaction, user: discord.User = None
    ):
        await self.get_money(interaction, user)

    @app_commands.guild_only()
    async def get_money(
        self, interaction: discord.Interaction, user: discord.User = None
    ):
        if user is None:
            user = interaction.user
            first_person = True
        else:
            if user.bot:
                await interaction.response.send_message(
                    "You can only check humans", ephemeral=True
                )
                return
            first_person = False

        money = self.bot.get_user_data(user.id).money
        if first_person:
            await interaction.response.send_message(
                f"You have {money_str(money)}", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"{user.mention} has {money_str(money)}", ephemeral=True
            )


async def setup(bot: LoobiBot):
    await bot.add_cog(MoneyCommand(bot))

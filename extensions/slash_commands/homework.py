from main import *


@app_commands.user_install()
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
class HomeworkCommand(
    commands.GroupCog,
    name="homework",
    description="Manage your homework list. \n"
    "Note: if you are not gdebest69 and you use this its pretty poggers",
):
    def __init__(self, bot: LoobiBot):
        self.bot = bot

    def has_hw(self, user: discord.User):
        if self.bot.get_user_data(user.id) is None:
            return False
        hm_list = self.bot.get_user_data(user.id).homeworks
        if not hm_list:
            return False
        return True

    def fetch_questions(self, questions: str):
        """Convert "a,b,c,...,z" or "a-z" (a, z are numbers) to [a, b, c, ..., z]
        Return None if can't format"""
        if "-" in questions:
            limits = questions.split("-")
            if len(limits) == 2 and limits[0].isdigit() and limits[1].isdigit():
                start = int(limits[0])
                end = int(limits[1])
                if end > start and end - start < 50:
                    question_list = [
                        str(question) for question in range(start, end + 1)
                    ]
                    return question_list
                return None
            else:
                return None
        else:
            question_list = questions.split(",")
            if not question_list:
                return None
            return question_list

    @app_commands.command(name="add", description="Add homework to your homework list")
    @app_commands.describe(
        name="The name of the homework",
        questions="The question numbers. Syntax: a,b,c,...,z or a-z (a, z are numbers)",
    )
    async def homework_add(
        self, interaction: discord.Interaction, name: str, questions: str
    ):
        question_list = self.fetch_questions(questions)
        if question_list is None:
            await interaction.response.send_message(
                ephemeral=True,
                content="Invalid questions syntax.\n"
                "Syntax: a,b,c,...,z or a-z (a, z are numbers)",
            )
        else:
            hm = HomeWork(name, question_list)
            self.bot.get_user_data(interaction.user.id).homeworks.append(hm)
            await interaction.response.send_message(
                ephemeral=True, content=f"Successfully added {hm} to your homework list"
            )

    @app_commands.command(
        name="see-all", description="Get a full list of your homework"
    )
    async def homework_see_all(self, interaction: discord.Interaction):
        if not self.has_hw(interaction.user):
            await interaction.response.send_message(
                ephemeral=True, content="You have no homework 😁"
            )
            return

        hm_list = self.bot.get_user_data(interaction.user.id).homeworks
        all_hm_list = [hm_list[0].as_first()]
        all_hm_list += [str(hm) for hm in hm_list[1:]]
        await interaction.response.send_message(
            ephemeral=True, content="Your homework list is:\n " + "\n".join(all_hm_list)
        )

    @app_commands.command(
        name="see-current", description="Get your current list of homework"
    )
    async def homework_see_current(self, interaction: discord.Interaction):
        if not self.has_hw(interaction.user):
            await interaction.response.send_message(
                ephemeral=True, content="You have no homework 😁"
            )
            return

        hm_list = self.bot.get_user_data(interaction.user.id).homeworks
        await interaction.response.send_message(
            ephemeral=True,
            content=f"Your current homework is:\n " f"{hm_list[0].as_first()}",
        )

    @app_commands.command(
        name="mark-as-done-current-question",
        description="Remove the first question from your current list of homework",
    )
    async def homework_long_name(self, interaction: discord.Interaction):
        if not self.has_hw(interaction.user):
            await interaction.response.send_message(
                ephemeral=True, content="You have no homework 😁"
            )
            return

        hm_list = self.bot.get_user_data(interaction.user.id).homeworks
        hm_list[0].question_list.pop(0)
        if not hm_list[0].question_list:
            hm_list.pop(0)
        if not hm_list:
            added_message = "You have no homework 😁"
        else:
            added_message = f"Your current questions are:\n {hm_list[0].as_first()}"
        await interaction.response.send_message(
            ephemeral=True,
            content="Successfully marked as done and removed the "
            "current question from your homework list\n"
            f"{added_message}",
        )

    @app_commands.command(
        name="remove-all-current-questions",
        description="Remove your current list of homework",
    )
    async def homework_long_name_2(self, interaction: discord.Interaction):
        if not self.has_hw(interaction.user):
            await interaction.response.send_message(
                ephemeral=True, content="You have no homework 😁"
            )
            return

        hm_list = self.bot.get_user_data(interaction.user.id).homeworks
        hm_list.pop(0)
        if not hm_list:
            added_message = "You have no homework 😁"
        else:
            added_message = f"Your current questions are:\n {hm_list[0].as_first()}"
        await interaction.response.send_message(
            ephemeral=True,
            content="Successfully marked as done and removed your "
            "current questions from your homework list\n"
            f"{added_message}",
        )

    @app_commands.command(name="remove-all", description="Clear your homework list")
    async def homework_remove_all(self, interaction: discord.Interaction):
        if not self.has_hw(interaction.user):
            await interaction.response.send_message(
                ephemeral=True, content="You have no homework 😁"
            )
            return

        self.bot.get_user_data(interaction.user.id).homeworks = []
        await interaction.response.send_message(
            ephemeral=True, content="Successfully cleared your homework list"
        )


async def setup(bot: LoobiBot):
    await bot.add_cog(HomeworkCommand(bot))

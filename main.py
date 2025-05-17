import pickle
import os
from discord.ext import commands
from settings import *
from utils import *


class HomeWork:
    def __init__(self, name: str, question_list: list[str]):
        self.name = name
        self.question_list = question_list

    def __str__(self):
        return f"{self.name}: {', '.join(self.question_list)}"

    def as_first(self):
        if len(self.question_list) == 1:
            return f"{self.name}: **{self.question_list[0]}**"
        return f"{self.name}: **{self.question_list[0]}**, {', '.join(self.question_list[1:])}"


class GuildData:
    def __init__(
        self,
        private_channels: dict[int, int] = None,
        karma: dict[int, int] = None,
        roles: dict[int, list[int]] = None,
        private_channel_roles_id: list[int] = None,
        nick_all_roles_id: list[int] = None,
        dj_roles_id: list[int] = None,
        default_karma_amount: int = DEFAULT_KARMA_AMOUNT,
        private_channels_category_id: int = 0,
        karma_points: dict[int, int] = None,
        disabled_commands: list[str] = None,
        disabled_channels: list[int] = None,
        game_status_channels_id: list[int] = None,
        n_words: dict[int, int] = None,
        auto_roles_enabled: bool = False,
    ):
        if n_words is None:
            n_words = {}
        if game_status_channels_id is None:
            game_status_channels_id = []
        if disabled_channels is None:
            disabled_channels = []
        if disabled_commands is None:
            disabled_commands = []
        if karma_points is None:
            karma_points = {}
        if dj_roles_id is None:
            dj_roles_id = []
        if nick_all_roles_id is None:
            nick_all_roles_id = []
        if private_channel_roles_id is None:
            private_channel_roles_id = []
        if roles is None:
            roles = {}
        if karma is None:
            karma = {}
        if private_channels is None:
            private_channels = {}
        self.private_channels = private_channels
        self.karma = karma
        self.roles = roles
        self.private_channel_roles_id = private_channel_roles_id
        self.nick_all_roles_id = nick_all_roles_id
        self.dj_roles_id = dj_roles_id
        self.default_karma_amount = default_karma_amount
        self.private_channels_category_id = private_channels_category_id
        self.karma_points = karma_points
        self.disabled_commands = disabled_commands
        self.disabled_channels = disabled_channels
        self.game_status_channels_id = game_status_channels_id
        self.n_words = n_words
        self.auto_roles_enabled = auto_roles_enabled

    def update(self):
        if not hasattr(self, "auto_roles_enabled"):
            self.auto_roles_enabled = False


class UserData:
    def __init__(self, homeworks: list[HomeWork] = None, money: int = 100):
        if homeworks is None:
            homeworks = []
        self.homeworks = homeworks
        self.money = money

    def update(self):
        pass


class LoobiBot(commands.Bot):
    def __init__(self, **options):
        self.music = JMusicBot(in_folder("music_bot"))
        intents = discord.Intents.default()
        intents.members = True
        intents.presences = True
        intents.message_content = True
        self.logger = logging.getLogger("loobibot")
        super().__init__(
            intents=intents,
            command_prefix="!",
            activity=discord.Game(f"/help | {self.music.prefix}help"),
            help_command=None,
            **options,
        )

        self.__guilds_data: dict[int, GuildData] = {}
        self.__users_data: dict[int, UserData] = {}
        self.vacation: bool = False
        self.tree.interaction_check = self.interaction_check
        self.testing = "-test" in sys.argv
        self.load_data()

        self.game_command = app_commands.Group(
            name="game",
            description="Play the stupid games I made",
            allowed_installs=app_commands.AppInstallationType(guild=True, user=False),
        )
        self.add_commands_to_tree(self.game_command)

        self.synced = False

    def load_data(self):
        try:
            with open(in_folder("data.lb"), "rb") as file:
                data: dict = pickle.load(file)
                self.__guilds_data = data["guilds"]
                self.__users_data = data["users"]
                self.vacation = data["vacation"]
                self.server_list_message = data.get("server_list_message", (0, 0))
        except Exception as e:
            if not isinstance(e, FileNotFoundError):
                with open(in_folder("data.lb"), "rb") as reader_file:
                    with open(in_folder("data_backup.lb"), "wb") as writer_file:
                        writer_file.write(reader_file.read())
            self.logger.warning(e)
            self.logger.warning("Using empty data")
            self.__guilds_data = {}
            self.__users_data = {}
            self.vacation = False
            self.server_list_message = (0, 0)

    def save_data(self):
        with open(in_folder("data.lb"), "wb") as file:
            pickle.dump(
                {
                    "guilds": self.__guilds_data,
                    "users": self.__users_data,
                    "vacation": self.vacation,
                    "server_list_message": self.server_list_message,
                },
                file,
            )

    def add_commands_to_tree(self, *commands):
        for command in commands:
            self.tree.add_command(command)

    def get_guild_data(self, guild_id: int):
        if guild_id in self.__guilds_data:
            return self.__guilds_data[guild_id]
        return None

    def get_user_data(self, user_id: int):
        if user_id in self.__users_data:
            return self.__users_data[user_id]
        if isinstance(user_id, int):
            self.set_user_data(user_id, UserData())
            return self.get_user_data(user_id)
        return None

    def set_guild_data(self, guild_id: int, guild_data: GuildData):
        self.__guilds_data[guild_id] = guild_data

    def set_user_data(self, user_id: int, user_data: UserData):
        self.__users_data[user_id] = user_data

    def update_data(self):
        for user_data in self.__users_data.values():
            user_data.update()
        for guild_data in self.__guilds_data.values():
            guild_data.update()

    async def interaction_check(self, interaction: discord.Interaction):
        # ignore auto complete interactions
        if interaction.type == discord.InteractionType.autocomplete:
            return True
        # printing the command to the console
        print_command(interaction, self.logger)
        # update user data if missing
        if self.get_user_data(interaction.user.id) is None:
            self.set_user_data(interaction.user.id, UserData())
        # ignore any restrictions if the command is only user installed
        if is_user_installed(interaction.command) and not is_guild_installed(
            interaction.command
        ):
            return True
        # update guild data if missing
        if (
            not is_in_dm(interaction)
            and self.get_guild_data(interaction.guild_id) is None
        ):
            self.set_guild_data(interaction.guild_id, GuildData())
        # if is in dm or the user is an admin ignore any guild commands restrictions
        if (
            interaction.channel.type == discord.ChannelType.private
            or interaction.user.guild_permissions.administrator
        ):
            return True
        # check guild commands restrictions
        if (
            interaction.channel.id
            in self.get_guild_data(interaction.guild_id).disabled_channels
        ):
            await interaction.response.send_message(
                "You can't use my commands in this channel", ephemeral=True
            )
            return False
        if (
            isinstance(interaction.command, app_commands.ContextMenu)
            or interaction.command.root_parent is None
        ):
            root_name = interaction.command.name
        else:
            root_name = interaction.command.root_parent.name
        if root_name in self.get_guild_data(interaction.guild_id).disabled_commands:
            await interaction.response.send_message(
                "This command is disabled on this server", ephemeral=True
            )
            return False

        return True

    async def on_command_error(self, ctx, error):
        if (
            isinstance(error, commands.CommandNotFound)
            or isinstance(error, commands.MissingRequiredArgument)
            or isinstance(error, commands.CheckFailure)
        ):
            return
        await super().on_command_error(ctx, error)

    async def on_error(self, event_method: str, /, *args, **kwargs) -> None:
        print(event_method, args, kwargs, sep="\n")
        return await super().on_error(event_method, *args, **kwargs)

    async def add_extensions(self, folder: str):
        for file in os.listdir(in_folder(folder)):
            if os.path.isdir(os.path.join(in_folder(folder), file)):
                await self.add_extensions(os.path.join(folder, file))
            elif file.endswith(".py"):
                extension_name = (
                    folder.replace(os.path.sep, ".")
                    + "."
                    + file[:-3]  # removing the .py extension
                )
                await self.load_extension(extension_name)

    async def setup_hook(self):
        self.update_data()

    async def on_ready(self):
        await self.wait_until_ready()

        if not self.synced:
            self.logger.info("Adding extensions")
            await self.add_extensions("extensions")

            if len(sys.argv) == 3:
                try:
                    resumed_channel = bot.get_channel(int(sys.argv[1]))
                    message = await resumed_channel.fetch_message(int(sys.argv[2]))
                    await message.edit(content="Successfully resumed the bot")
                except Exception as e:
                    self.logger.warning(e)

            self.synced = True

        self.logger.info(f"{self.user} is ready")


if __name__ == "__main__":
    import logging

    discord.utils.setup_logging()
    logging.getLogger("discord.gateway").setLevel(logging.WARNING)
    bot = LoobiBot()
    bot.run(TOKEN, log_handler=None)

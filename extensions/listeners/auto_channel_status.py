import json
from io import StringIO
from discord import ui
from components.settings_view import SettingsView, ManageChannelsSelect
from main import *

transformer: dict[str, list[str] | dict[str, str]] = None


class ActivityTransformerActionRow(ui.ActionRow[SettingsView]):
    def __init__(self, guild_data: GuildData):
        super().__init__()
        self.guild_data = guild_data
        self.activity_transformer = guild_data.activity_transformer
        self.update_button()

    def update_button(self):
        (
            self.toggle_activity_transformer.label,
            self.toggle_activity_transformer.style,
        ) = (
            ("Disable activity transformer", discord.ButtonStyle.red)
            if self.activity_transformer
            else ("Enable activity transformer", discord.ButtonStyle.green)
        )

    @ui.button()
    async def toggle_activity_transformer(
        self, interaction: discord.Interaction, button: ui.Button
    ):
        self.activity_transformer = not self.activity_transformer
        self.guild_data.activity_transformer = self.activity_transformer
        self.update_button()
        await interaction.response.edit_message(view=self.view)

    @ui.button(label="View transformer JSON", style=discord.ButtonStyle.blurple)
    async def view_transformer_json(
        self, interaction: discord.Interaction, button: ui.Button
    ):
        await interaction.response.send_message(
            file=discord.File(
                StringIO(json.dumps(transformer, indent=4)),
                filename="activity_transformer.json",
            ),
            ephemeral=True,
        )


class ActivityStatusSettingsView(SettingsView):
    def __init__(self, guild_data: GuildData, back_view_factory):
        super().__init__()
        container = ui.Container()
        container.add_item(ui.TextDisplay("# Activity status settings"))
        container.add_item(
            ui.Separator(visible=False, spacing=discord.SeparatorSpacing.large)
        )
        container.add_item(ui.TextDisplay("Activity status channels"))
        container.add_item(
            ManageChannelsSelect(
                guild_data.game_status_channels_id,
                "Select channels to have auto activity status",
                [discord.ChannelType.voice],
            )
        )
        container.add_item(ui.Separator())
        container.add_item(ActivityTransformerActionRow(guild_data))
        container.add_item(
            ui.TextDisplay(
                "If activity transformer is enabled, the same activities will be grouped together,"
                ' for example: "Among Us with Medal" and "Among Us" will be shown as "Among Us"'
            )
        )
        self.add_item(container)
        self.add_back_button(back_view_factory)


class AutoChannelStatus(commands.Cog):
    def __init__(self, bot: LoobiBot):
        self.bot = bot
        self.ignored_channels_id: set[int] = set()
        global transformer
        transformer = self.load_activity_transformer()

    def load_activity_transformer(self) -> dict[str, list[str] | dict[str, str]]:
        try:
            with open(in_folder("activity_transformer.json"), "r") as file:
                activity_transformer = json.load(file)
                if "prefixes" not in activity_transformer:
                    activity_transformer["prefixes"] = []
                if "suffixes" not in activity_transformer:
                    activity_transformer["suffixes"] = []
                if "replacements" not in activity_transformer:
                    activity_transformer["replacements"] = {}
        except FileNotFoundError:
            activity_transformer = {
                "prefixes": [],
                "suffixes": [],
                "replacements": {},
            }
        return activity_transformer

    def get_main_activity(self, member: discord.Member):
        activities = member.activities
        main_activity = discord.utils.find(
            lambda activity: not isinstance(activity, discord.Game)
            and activity.type == discord.ActivityType.playing,
            activities,
        )
        if main_activity is None:
            main_activity = discord.utils.get(
                activities, type=discord.ActivityType.playing
            )
        return main_activity

    def transform_activity_name(self, activity_name: str) -> str:
        # Remove prefixes
        for prefix in transformer["prefixes"]:
            if activity_name.startswith(prefix):
                activity_name = activity_name.removeprefix(prefix)
                break
        # Remove suffixes
        for suffix in transformer["suffixes"]:
            if activity_name.endswith(suffix):
                activity_name = activity_name.removesuffix(suffix)
                break
        # Replace names
        new_name = transformer["replacements"].get(activity_name)
        if new_name is not None:
            activity_name = new_name

        return activity_name

    async def update_status(
        self, member: discord.Member, channel: discord.VoiceChannel = None
    ):
        if member.bot:
            return

        if member.voice is not None or channel is not None:
            if channel is None:
                channel = member.voice.channel
            if (
                channel.id in self.ignored_channels_id
                or channel.id
                not in self.bot.get_guild_data(channel.guild.id).game_status_channels_id
            ):
                return

            games: dict[str | None, int] = {}
            players_count = 0
            non_players_count = 0
            for member in channel.members:
                if member.bot:
                    continue

                activity = self.get_main_activity(member)
                if activity is None:
                    game_name = None
                    non_players_count += 1
                else:
                    game_name = (
                        self.transform_activity_name(activity.name)
                        if self.bot.get_guild_data(member.guild.id).activity_transformer
                        else activity.name
                    )
                    players_count += 1
                if game_name in games:
                    games[game_name] += 1
                else:
                    games[game_name] = 1
            games = dict(
                sorted(
                    [(key, value) for key, value in games.items()],
                    reverse=True,
                    key=lambda x: x[1],
                )
            )
            if None in games:
                games.pop(None)
            if (
                players_count >= non_players_count or players_count > 1
            ) and players_count > 0:
                status = ", ".join(games.keys())
            else:
                status = None
            if status == channel.status:
                return
            try:
                await channel.edit(status=status, reason="Activity status")
            except discord.errors.DiscordServerError:
                pass
            except discord.Forbidden:
                pass

    @commands.Cog.listener()
    async def on_voice_state_update(
        self, member, before: discord.VoiceState, after: discord.VoiceState
    ):
        if before.channel is not None and not before.channel.members:
            self.ignored_channels_id.discard(before.channel.id)
        await self.update_status(member, before.channel)
        await self.update_status(member, after.channel)

    @commands.Cog.listener()
    async def on_presence_update(self, before, after):
        await self.update_status(after)

    @commands.Cog.listener()
    async def on_audit_log_entry_create(self, entry: discord.AuditLogEntry):
        if (
            entry.user is not None
            and not entry.user.bot
            and (
                entry.action == discord.AuditLogAction.voice_channel_status_update
                or entry.action == discord.AuditLogAction.voice_channel_status_delete
            )
        ):
            channel = entry.target
            if isinstance(channel, discord.VoiceChannel):
                self.ignored_channels_id.add(channel.id)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if message.author.id == OWNER_ID and message.content == "/update_transformer":
            global transformer
            transformer = self.load_activity_transformer()
            await message.reply("Activity transformer updated", mention_author=False)


async def setup(bot: LoobiBot):
    await bot.add_cog(AutoChannelStatus(bot))

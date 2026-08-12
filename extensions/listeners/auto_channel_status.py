from discord import ui
from components.settings_view import SettingsView, ManageChannelsSelect
from main import *


class ToggleMedalRemovalButton(ui.ActionRow[SettingsView]):
    def __init__(self, guild_data: GuildData):
        super().__init__()
        self.guild_data = guild_data
        self.remove_medal = guild_data.remove_medal
        self.update_button()

    def update_button(self):
        self.toggle_medal_removal.label, self.toggle_medal_removal.style = (
            ('Ignore "with Medal" text', discord.ButtonStyle.red)
            if self.remove_medal
            else ('Remove "with Medal" from games names', discord.ButtonStyle.green)
        )

    @ui.button()
    async def toggle_medal_removal(
        self, interaction: discord.Interaction, button: ui.Button
    ):
        self.remove_medal = not self.remove_medal
        self.guild_data.remove_medal = self.remove_medal
        self.update_button()
        await interaction.response.edit_message(view=self.view)


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
        container.add_item(ToggleMedalRemovalButton(guild_data))
        self.add_item(container)
        self.add_back_button(back_view_factory)


class AutoChannelStatus(commands.Cog):
    def __init__(self, bot: LoobiBot):
        self.bot = bot
        self.ignored_channels_id: set[int] = set()

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

    async def update_status(
        self, member: discord.Member, channel: discord.VoiceChannel = None
    ):
        if member.bot:
            return

        remove_medal = self.bot.get_guild_data(member.guild.id).remove_medal

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
                        activity.name.removesuffix(" with Medal")
                        if remove_medal
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


async def setup(bot: LoobiBot):
    await bot.add_cog(AutoChannelStatus(bot))

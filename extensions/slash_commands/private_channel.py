from asyncio import create_task
from discord import ui, ButtonStyle
from components.settings_view import SettingsView, ManageRolesSelect
from main import *


class PrivateChannelsCategorySelect(ui.ActionRow["PrivateChannelSettingsView"]):
    def __init__(self, bot: LoobiBot, guild: discord.Guild):
        super().__init__()
        self.bot = bot
        self.guild = guild
        self.set_default_value()

    def set_default_value(self):
        guild_data = self.bot.get_guild_data(self.guild.id)
        category_id = guild_data.private_channels_category_id
        category = self.guild.get_channel(category_id)
        self.select_category.default_values = [category] if category is not None else []

    @ui.select(
        placeholder="Select category",
        channel_types=[discord.ChannelType.category],
        min_values=0,
        max_values=1,
        cls=ui.ChannelSelect,
    )
    async def select_category(
        self,
        interaction: discord.Interaction,
        select: ui.ChannelSelect,
    ):
        category_id = select.values[0].id if select.values else 0
        guild_data = self.bot.get_guild_data(self.guild.id)
        guild_data.private_channels_category_id = category_id
        self.set_default_value()
        await interaction.response.edit_message(view=self.view)


class MovePrivateChannelsButton(ui.ActionRow["PrivateChannelSettingsView"]):
    def __init__(self, bot: LoobiBot, guild: discord.Guild):
        super().__init__()
        self.bot = bot
        self.guild = guild

    @ui.button(
        label="Move all private channels to the category", style=ButtonStyle.blurple
    )
    async def move_private_channels(
        self, interaction: discord.Interaction, button: ui.Button
    ):
        create_task(interaction.response.defer())
        guild_data = self.bot.get_guild_data(self.guild.id)
        category = self.guild.get_channel(guild_data.private_channels_category_id)
        for channel_id in guild_data.private_channels.values():
            channel = self.guild.get_channel(channel_id)
            if channel is not None and channel.category != category:
                try:
                    await channel.move(
                        category=category,
                        end=True,
                        reason="Moving private channels to the category",
                    )
                except discord.Forbidden:
                    pass


class PrivateChannelSettingsView(SettingsView):
    def __init__(self, bot: LoobiBot, guild: discord.Guild, back_view_factory):
        super().__init__()
        container = ui.Container()
        container.add_item(ui.TextDisplay("# Private channels settings"))
        container.add_item(
            ui.Separator(visible=False, spacing=discord.SeparatorSpacing.large)
        )
        container.add_item(ui.TextDisplay("Required roles"))
        container.add_item(
            ManageRolesSelect(
                bot.get_guild_data(guild.id).private_channel_roles_id,
                "Select required roles",
            )
        )
        container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay("Private channels category"))
        container.add_item(PrivateChannelsCategorySelect(bot, guild))
        container.add_item(MovePrivateChannelsButton(bot, guild))
        self.add_item(container)
        self.add_back_button(back_view_factory)


@app_commands.guild_only()
@app_commands.allowed_installs(guilds=True, users=False)
class PrivateChannelCommand(
    commands.GroupCog,
    name="private-channel",
    description="Commands related to private channels",
):
    def __init__(self, bot: LoobiBot):
        self.bot = bot
        self.private_channel_creations: dict[int, set[int]] = (
            {}
        )  # caching users that are in the process of creating a private channel per guild

    async def interaction_check(self, interaction):
        # channel check
        if is_in_dm(interaction):
            await must_use_in_guild(interaction)
            return False
        return True

    async def cog_app_command_error(self, interaction, error):
        if isinstance(error, app_commands.CheckFailure):
            return
        return await super().cog_app_command_error(interaction, error)

    def is_creating_private_channel(self, user_id: int, guild_id: int) -> bool:
        return (
            guild_id in self.private_channel_creations
            and user_id in self.private_channel_creations[guild_id]
        )

    def add_creating_private_channel(self, user_id: int, guild_id: int):
        if guild_id not in self.private_channel_creations:
            self.private_channel_creations[guild_id] = set()
        self.private_channel_creations[guild_id].add(user_id)

    def remove_creating_private_channel(self, user_id: int, guild_id: int):
        if guild_id in self.private_channel_creations:
            self.private_channel_creations[guild_id].discard(user_id)
            if not self.private_channel_creations[guild_id]:
                del self.private_channel_creations[guild_id]

    @app_commands.command(name="create", description="Create a private channel")
    @app_commands.choices(
        channel_type=[
            app_commands.Choice(name="Text", value="text"),
            app_commands.Choice(name="Voice", value="voice"),
        ]
    )
    @app_commands.describe(
        channel_type="The type of the channel", name="The name of the channel"
    )
    @app_commands.rename(channel_type="type")
    async def channel_create(
        self,
        interaction: discord.Interaction,
        channel_type: app_commands.Choice[str],
        name: str,
    ):
        # roles check
        private_channel_roles_id = self.bot.get_guild_data(
            interaction.guild_id
        ).private_channel_roles_id
        if not has_one_of_roles(interaction.user, private_channel_roles_id):
            await send_invalid_permission(interaction, private_channel_roles_id)
            return

        # private channel check
        if self.is_creating_private_channel(interaction.user.id, interaction.guild_id):
            await interaction.response.send_message(
                "You are already in the process of creating a private channel",
                ephemeral=True,
            )
            return
        private_channels = self.bot.get_guild_data(
            interaction.guild_id
        ).private_channels
        if interaction.user.id in private_channels:
            channel = self.bot.get_channel(private_channels[interaction.user.id])
            if channel is not None:
                await interaction.response.send_message(
                    f"You already have a private channel - {channel.mention}",
                    ephemeral=True,
                )
                return

        # create private channel
        self.add_creating_private_channel(interaction.user.id, interaction.guild_id)
        thinking_task = create_task(interaction.response.defer(ephemeral=True))
        private_channels_category_id = self.bot.get_guild_data(
            interaction.guild_id
        ).private_channels_category_id
        category = self.bot.get_channel(private_channels_category_id)
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(
                read_messages=False
            ),
            interaction.user: discord.PermissionOverwrite(
                **{perm: value for perm, value in discord.Permissions.all()}
            ),
        }
        try:
            if channel_type.value == "text":
                channel = await interaction.guild.create_text_channel(
                    name, category=category, overwrites=overwrites
                )
            elif channel_type.value == "voice":
                channel = await interaction.guild.create_voice_channel(
                    name, category=category, overwrites=overwrites
                )
            else:
                await thinking_task
                await interaction.edit_original_response(
                    content=f"Invalid channel type: {channel_type.value}"
                )
                self.remove_creating_private_channel(
                    interaction.user.id, interaction.guild_id
                )
                return
            private_channels[interaction.user.id] = channel.id
            self.remove_creating_private_channel(
                interaction.user.id, interaction.guild_id
            )
            await thinking_task
            await interaction.edit_original_response(
                content=f"Successfully created your private channel - {channel.mention}"
            )
        except Exception as e:
            self.remove_creating_private_channel(
                interaction.user.id, interaction.guild_id
            )
            await thinking_task
            if isinstance(e, discord.Forbidden):
                await interaction.edit_original_response(
                    content="Sorry, but I can't create a private channel due to lack of permissions in this server",
                )
            else:
                await interaction.edit_original_response(
                    content="Something went wrong when trying to create a private channel,"
                    + f" if this problem continues, please report it to {mention_user(OWNER_ID)}",
                )
                raise e

    @app_commands.command(name="delete", description="Delete your private channel")
    async def channel_delete(self, interaction: discord.Interaction):
        private_channels = self.bot.get_guild_data(
            interaction.guild_id
        ).private_channels
        if interaction.user.id in private_channels:
            channel = self.bot.get_channel(private_channels[interaction.user.id])
            if channel is None:
                await interaction.response.send_message(
                    "You don't have any private channel to delete", ephemeral=True
                )
            else:
                thinking_task = create_task(interaction.response.defer(ephemeral=True))
                try:
                    await channel.delete()
                    await thinking_task
                    if self.bot.get_channel(interaction.channel.id) is not None:
                        await interaction.edit_original_response(
                            content="Successfully deleted your private channel"
                        )
                except Exception as e:
                    await thinking_task
                    if isinstance(e, discord.Forbidden):
                        await interaction.edit_original_response(
                            content="Sorry, but I can't delete your private channel due to lack of permissions in this server",
                        )
                    else:
                        await interaction.edit_original_response(
                            content="Something went wrong when trying to delete your private channel,"
                            + f" if this problem continues, please report it to {mention_user(OWNER_ID)}",
                        )
                        raise e
        else:
            await interaction.response.send_message(
                "You don't have any private channel to delete", ephemeral=True
            )

    @app_commands.command(
        name="redeem",
        description="Get back your permissions in your private channel if you lost them",
    )
    async def channel_redeem(self, interaction: discord.Interaction):
        private_channels = self.bot.get_guild_data(
            interaction.guild_id
        ).private_channels
        if interaction.user.id in private_channels:
            channel = self.bot.get_channel(private_channels[interaction.user.id])
            if channel is None:
                await interaction.response.send_message(
                    "You don't have any private channel to redeem", ephemeral=True
                )
            else:
                thinking_task = create_task(interaction.response.defer(ephemeral=True))
                try:
                    await channel.set_permissions(
                        interaction.user,
                        **{perm: value for perm, value in discord.Permissions.all()},
                    )
                    await thinking_task
                    await interaction.edit_original_response(
                        content="Successfully redeemed your private channel"
                    )
                except Exception as e:
                    await thinking_task
                    if isinstance(e, discord.Forbidden):
                        await interaction.edit_original_response(
                            content="Sorry, but I can't redeem your private channel due to lack of permissions in this server",
                        )
                    else:
                        await interaction.edit_original_response(
                            content="Something went wrong when trying to redeem your private channel,"
                            + f" if this problem continues, please report it to {mention_user(OWNER_ID)}",
                        )
                        raise e
        else:
            await interaction.response.send_message(
                "You don't have any private channel to redeem", ephemeral=True
            )

    @app_commands.command(
        name="list", description="A list of all the private channels and their owners"
    )
    async def channel_list(self, interaction: discord.Interaction):
        # permission check
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "You must have administrator permissions to use this command",
                ephemeral=True,
            )
            return

        private_channels = self.bot.get_guild_data(
            interaction.guild_id
        ).private_channels
        members_list = []
        channels_list = []
        for user_id in private_channels:
            channel = self.bot.get_channel(private_channels[user_id])
            if channel is not None:
                members_list.append(mention_user(user_id))
                channels_list.append(channel.mention)
        if not members_list:
            await interaction.response.send_message(
                "There aren't any private channels", ephemeral=True
            )
            return
        members_str = "\n".join(members_list)
        channels_str = "\n".join(channels_list)
        embed = discord.Embed(color=EMBED_COLOR, title="Private channels")
        embed.add_field(name="Members", value=members_str, inline=True)
        embed.add_field(name="Channels", value=channels_str, inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: LoobiBot):
    await bot.add_cog(PrivateChannelCommand(bot))

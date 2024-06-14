from main import *


@app_commands.guild_only()
class PrivateChannelCommand(
    commands.GroupCog,
    name="private-channel",
    description="Commands related to private channels",
):
    def __init__(self, bot: LoobiBot):
        self.bot = bot

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
        # channel check
        if is_in_dm(interaction):
            await must_use_in_guild(interaction)
            return

        # roles check
        private_channel_roles_id = self.bot.get_guild_data(
            interaction.guild_id
        ).private_channel_roles_id
        if not has_one_of_roles(interaction.user, private_channel_roles_id):
            await send_invalid_permission(interaction, private_channel_roles_id)
            return

        # private channel check
        private_channels = self.bot.get_guild_data(
            interaction.guild_id
        ).private_channels
        if interaction.user.id in private_channels:
            if (
                private_channels[interaction.user.id] == 0
            ):  # the user is currently making a private channel
                await interaction.response.send_message(
                    "You are already in the process of making a private channel",
                    ephemeral=True,
                )
                return
            channel = self.bot.get_channel(private_channels[interaction.user.id])
            if channel is not None:
                await interaction.response.send_message(
                    f"You already have a private channel - {channel.mention}",
                    ephemeral=True,
                )
                return

        private_channels[interaction.user.id] = 0
        await interaction.response.defer(ephemeral=True)
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
                await interaction.edit_original_response(
                    content=f"Invalid channel type: {channel_type.value}"
                )
                private_channels[interaction.user.id] = -1
                return
            private_channels[interaction.user.id] = channel.id
            await interaction.edit_original_response(
                content=f"Successfully created your private channel - {channel.mention}"
            )
        except Exception as e:
            private_channels[interaction.user.id] = -1
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
        # channel check
        if is_in_dm(interaction):
            await must_use_in_guild(interaction)
            return

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
                await interaction.response.defer(ephemeral=True)
                try:
                    await channel.delete()
                    if self.bot.get_channel(interaction.channel.id) is not None:
                        await interaction.edit_original_response(
                            content="Successfully deleted your private channel"
                        )
                except Exception as e:
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
        # channel check
        if is_in_dm(interaction):
            await must_use_in_guild(interaction)
            return

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
                await interaction.response.defer(ephemeral=True)
                try:
                    await channel.set_permissions(
                        interaction.user,
                        **{perm: value for perm, value in discord.Permissions.all()},
                    )
                    await interaction.edit_original_response(
                        content="Successfully redeemed your private channel"
                    )
                except Exception as e:
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
        # channel check
        if is_in_dm(interaction):
            await must_use_in_guild(interaction)
            return

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
        await interaction.response.send_message(embed=embed)


async def setup(bot: LoobiBot):
    await bot.add_cog(PrivateChannelCommand(bot))

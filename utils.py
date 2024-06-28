import os.path
import sys
import discord
import datetime
import settings
import json
import re
import aiohttp
from discord import app_commands


def time_prefix():
    return f"[{datetime.datetime.now().isoformat(sep=' ', timespec='seconds')}]"


def print_command(interaction: discord.Interaction, logger):
    # print(interaction.data)
    """for key, value in interaction.namespace:
    print(key, value, sep=": ")"""

    if is_in_dm(interaction):
        prefix = f"[Direct message] {interaction.user}"
    elif is_in_gc(interaction):
        prefix = f"[{interaction.channel}] {interaction.user}"
    else:
        if isinstance(interaction.channel, discord.Thread):
            channel_prefix = f"{interaction.channel.parent} -> {interaction.channel}"
        else:
            channel_prefix = interaction.channel
        prefix = f"[{interaction.guild}: {channel_prefix}] {interaction.user}"

    if isinstance(interaction.command, app_commands.Command):
        command = (
            interaction.command.qualified_name
            + " "
            + " ".join([str(parm[1]) for parm in interaction.namespace])
        )
        logger.info(f"{prefix}: /{command}")

    elif isinstance(interaction.command, app_commands.ContextMenu):

        def get_target(interaction: discord.Interaction):
            if "users" in interaction.data["resolved"]:
                users_data = interaction.data["resolved"]["users"]
                for user_data in users_data.values():
                    username = user_data["username"]
                    discriminator = user_data["discriminator"]
                    if discriminator != "0":
                        username += "#" + discriminator
                    return username, discord.User
            elif "messages" in interaction.data["resolved"]:
                messages_data = interaction.data["resolved"]["messages"]
                for message_data in messages_data.values():
                    guild_id = (
                        interaction.guild_id if is_in_guild(interaction) else "@me"
                    )
                    target = (
                        f"https://discord.com/channels/{guild_id}"
                        + f"/{interaction.channel_id}/{message_data['id']}"
                    )
                    return target, discord.Message

        target, target_type = get_target(interaction)
        if target_type == discord.Message:
            logger.info(
                f"{prefix} used {interaction.command.name} on the following message: {target}"
            )
        elif target_type == discord.User:
            logger.info(f"{prefix} used {interaction.command.name} on {target}")


def print_message(message: discord.Message, logger):
    if is_in_dm(message):
        prefix = f"[Direct message] {message.author.name}"
    else:
        prefix = f"[{message.guild.name}: {message.channel.name}] {message.author.name}"
    logger.info(f"{prefix}: {message.content}")


def is_connected(bot: discord.Client, channel: discord.VoiceChannel):
    for voice_client in bot.voice_clients:
        if voice_client.channel == channel:
            return True
    return False


def has_one_of_roles(
    member: discord.Member, roles_id: list[int], *, ignore_admin=False
):
    if not ignore_admin and member.guild_permissions.administrator:
        return True
    for role_id in roles_id:
        for role in member.roles:
            if role_id == role.id:
                return True
    return False


def has_role(member: discord.Member, role_id: int):
    for role in member.roles:
        if role_id == role.id:
            return True
    return False


async def send_invalid_permission(
    interaction: discord.Interaction, roles_id: list[int]
):
    guild = interaction.guild
    roles = [
        guild.get_role(role_id).mention
        for role_id in roles_id
        if guild.get_role(role_id) is not None
    ]
    message = " ".join(roles) if roles else str(None)
    embed = discord.Embed(
        description=message, color=settings.EMBED_COLOR, title="Required roles:"
    )
    await interaction.response.send_message(
        content="You don't have permission to use this command",
        embed=embed,
        ephemeral=True,
    )


async def get_user(bot: discord.Client, user_id: int):
    user = bot.get_user(user_id)
    if user is None:
        user = await bot.fetch_user(user_id)  # might still be None :o
    return user


def mention_user(user_id: int):
    return f"<@{user_id}>"


def sort_dict_by_value(d: dict, reverese: bool = False):
    return dict(sorted(d.items(), key=lambda item: item[1], reverse=reverese))


def is_in_dm(obj: discord.Message | discord.Interaction):
    return obj.channel.type == discord.ChannelType.private


def is_in_gc(obj: discord.Message | discord.Interaction):
    return obj.channel.type == discord.ChannelType.group


def is_in_guild(obj: discord.Message | discord.Interaction):
    return obj.guild is not None


async def must_use_in_guild(obj: discord.Message | discord.Interaction):
    if isinstance(obj, discord.Interaction):
        await obj.response.send_message(
            "You must use this command inside a server", ephemeral=True
        )
    elif isinstance(obj, discord.Message):
        await obj.reply(
            "You must use this command inside a server", mention_author=False
        )


def get_all_attr(__class):
    return [
        name
        for name, instance in vars(__class).items()
        if isinstance(instance, __class)
    ]


def in_folder(path: str):
    return os.path.join(sys.path[0], path)


def money_str(money: int):
    return f"{money:,}$"


def is_user_installed(
    command: app_commands.Command | app_commands.ContextMenu | app_commands.Group,
):
    if isinstance(command, app_commands.Command) and command.parent is not None:
        base_command = command.parent
    else:
        base_command = command
    return (
        base_command.allowed_installs is not None and base_command.allowed_installs.user
    )


def is_guild_installed(
    command: app_commands.Command | app_commands.ContextMenu | app_commands.Group,
):
    if isinstance(command, app_commands.Command) and command.parent is not None:
        base_command = command.parent
    else:
        base_command = command
    return base_command.allowed_installs is None or base_command.allowed_installs.guild


async def get_router_ip():
    ipify_url = "http://api.ipify.org"
    async with aiohttp.ClientSession() as session:
        async with session.get(ipify_url) as response:
            if response.status == 200:
                return await response.text()
            else:
                return None


def time_remaining(seconds: float):
    second = 1
    minute = second * 60
    hour = minute * 60
    day = hour * 24
    year = day * 365
    if seconds >= year:
        value = seconds // year
        t = "year"
    elif seconds >= day:
        value = seconds // day
        t = "day"
    elif seconds >= hour:
        value = seconds // hour
        t = "hour"
    elif seconds >= minute:
        value = seconds // minute
        t = "minute"
    else:
        value = seconds
        t = "second"
    if value != 1:
        t += "s"
    return f"{int(value)} {t}"


class JMusicBot:
    def __init__(self, path: str):
        self.path = path
        self.prefix = self.get_prefix()

    def get_server_settings_data(self):
        with open(os.path.join(self.path, "serversettings.json"), "r") as file:
            server_settings = json.load(file)
        return server_settings

    def get_dj_role(self, guild: discord.Guild):
        server_settings = self.get_server_settings_data()
        if str(guild.id) not in server_settings:
            return None
        guild_settings = server_settings[str(guild.id)]
        if "dj_role_id" not in guild_settings:
            return None
        dj_role_id = int(guild_settings["dj_role_id"])
        dj_role = guild.get_role(dj_role_id)
        return dj_role

    def get_prefix(self):
        with open(os.path.join(self.path, "config.txt")) as file:
            match = re.search(r'prefix = "(.*?)"', file.read())
            if match:
                # Extract the value of 'prefix' without quotes
                prefix_value = match.group(1)
                return prefix_value
            else:
                raise ValueError("Can't find the prefix of the music bot")

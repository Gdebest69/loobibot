from main import *


class HelpCommand(commands.Cog):
    def __init__(self, bot: LoobiBot):
        self.bot = bot

    async def help_auto_complete(
        self,
        interaction: discord.Interaction,
        current: str,
    ):
        command_list = [cmd.qualified_name for cmd in self.bot.tree.walk_commands()]
        if is_in_guild(interaction):
            command_list += [
                cmd.qualified_name
                for cmd in self.bot.tree.walk_commands(guild=interaction.guild)
            ]
        choices = [
            app_commands.Choice(name=cmd, value=cmd)
            for cmd in command_list
            if current.lower() in cmd.lower()
        ]
        return choices if len(choices) <= 25 else []

    @app_commands.command(name="help", description="Get help about any of my commands")
    @app_commands.describe(command="Specific command name")
    @app_commands.autocomplete(command=help_auto_complete)
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def help_command(self, interaction: discord.Interaction, command: str = None):
        if command is None:
            embed = discord.Embed(
                color=EMBED_COLOR, title=f"{self.bot.user.name} commands"
            )
            embed.set_footer(
                text="Use /help <command> to get details about a specific command",
                icon_url=self.bot.user.display_avatar.url,
            )
            if is_in_guild(interaction):
                guild_command_list = [
                    f"`/{cmd.qualified_name}`"
                    for cmd in self.bot.tree.get_commands(guild=interaction.guild)
                    if not isinstance(cmd, app_commands.ContextMenu)
                ]
                if guild_command_list:
                    embed.add_field(
                        name="Guild commands",
                        value=", ".join(guild_command_list),
                        inline=False,
                    )
            global_command_list = [
                f"`/{cmd.qualified_name}`"
                for cmd in self.bot.tree.get_commands()
                if not isinstance(cmd, app_commands.ContextMenu)
                and is_guild_installed(cmd)
            ]
            if global_command_list:
                embed.add_field(
                    name="Global commands",
                    value=", ".join(global_command_list),
                    inline=False,
                )
            user_command_list = [
                f"`/{cmd.qualified_name}`"
                for cmd in self.bot.tree.get_commands()
                if not isinstance(cmd, app_commands.ContextMenu)
                and is_user_installed(cmd)
            ]
            if user_command_list:
                embed.add_field(
                    name="User commands",
                    value=", ".join(user_command_list),
                    inline=False,
                )
            await interaction.response.send_message(
                embed=embed,
                ephemeral=True,
            )
        else:
            cmd = discord.utils.get(
                self.bot.tree.walk_commands(), qualified_name=command
            )
            if cmd is None:
                if not is_in_guild(interaction):
                    await interaction.response.send_message(
                        "Invalid command name", ephemeral=True
                    )
                    return
                cmd = discord.utils.get(
                    self.bot.tree.walk_commands(guild=interaction.guild),
                    qualified_name=command,
                )
                if cmd is None:
                    await interaction.response.send_message(
                        "Invalid command name", ephemeral=True
                    )
                    return

            if isinstance(cmd, app_commands.Group):
                embed = discord.Embed(
                    color=EMBED_COLOR,
                    title="Parent command",
                    description=f"`/{cmd.qualified_name}` - {cmd.description}",
                )
                group_command_list = [
                    f"`/{group_cmd.qualified_name}`"
                    for group_cmd in cmd.walk_commands()
                ]
                embed.add_field(name="Subcommands", value=", ".join(group_command_list))
            else:
                embed = discord.Embed(
                    color=EMBED_COLOR,
                    title="Command",
                    description=f"`/{cmd.qualified_name}` - {cmd.description}",
                )
                if cmd.parameters:
                    args = [
                        f"{parm.display_name}: {parm.description}"
                        for parm in cmd.parameters
                    ]
                    embed.add_field(name="Arguments", value="\n".join(args))

            base_command = cmd if cmd.parent is None else cmd.parent
            allowed_installs = []
            if is_guild_installed(base_command):
                allowed_installs.append("guild")
            if is_user_installed(base_command):
                allowed_installs.append("user")
            embed.add_field(
                name="Allowed installs",
                value=", ".join(allowed_installs),
                inline=False,
            )
            if base_command.allowed_contexts is not None:
                allowed_contexts = []
                if base_command.allowed_contexts.guild:
                    allowed_contexts.append("guild")
                if base_command.allowed_contexts.dm_channel:
                    allowed_contexts.append("DM channel")
                if base_command.allowed_contexts.private_channel:
                    allowed_contexts.append("group chat")
                embed.add_field(
                    name="Allowed contexts",
                    value=", ".join(allowed_contexts),
                    inline=False,
                )
            await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: LoobiBot):
    await bot.add_cog(HelpCommand(bot))

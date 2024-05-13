import discord
import sys
import os
import subprocess
import datetime
from settings import *

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)


def get_last_updated_time(folder_path):
    latest_mtime = 0

    # Traverse through the folder and its subfolders
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            mtime = os.path.getmtime(file_path)
            latest_mtime = max(latest_mtime, mtime)

    return datetime.datetime.fromtimestamp(latest_mtime)


@bot.event
async def on_ready():
    try:
        channel = bot.get_channel(int(sys.argv[1]))
        message = await channel.fetch_message(int(sys.argv[2]))
        await message.edit(content="Successfully paused the bot")
    except Exception as e:
        print(e)


@bot.event
async def on_message(message: discord.Message):
    if message.author.id == OWNER_ID and message.content == "/resume":
        resumed_message = await message.reply("Resuming bot...", mention_author=False)
        try:
            subprocess.run(["git", "pull"])
        except Exception as e:
            await message.channel.send(f"Error occurred while executing git pull: {e}")
            raise e
        os.execl(
            sys.executable,
            sys.executable,
            os.path.join(sys.path[0], "main.py"),
            str(message.channel.id),
            str(resumed_message.id),
        )

    if message.author.id == OWNER_ID and message.content == "/check":
        await message.reply(
            discord.utils.format_dt(get_last_updated_time(r".\\"), "R"),
            mention_author=False,
        )


bot.run(TOKEN)

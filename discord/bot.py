#!/usr/bin/env python3
import os
import sys
import asyncio
import importlib
from dotenv import load_dotenv

from colors import Colors
from colors import colorize as cl

from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

def can_import(module_name):
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False

assert can_import("discord"), cl("Please install discord.py:  pip install discord.py", Colors.RED)

import discord
from discord.ext import commands

from monitor import Monitor

# Load default environment variables (.env)
load_dotenv()

class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        asyncio.run(bot.add_cog(self))

    @commands.Cog.listener()
    async def on_ready(self):
        print(cl(f'{self.bot.user}', Colors.GREEN) + ' has connected to Discord!')
        await self.bot.tree.sync()

def run(app_id: str, token: str):
    intents = discord.Intents.all()
    intents.members = True
    intents.messages = True
    intents.reactions = True
    intents.message_content = True

    bot = commands.Bot(
        application_it=app_id,
        command_prefix='👶 ---> ',
        intents=intents
    )

    Admin(bot)
    Monitor(bot)

    bot.run(token)

if __name__ == "__main__":
    APP_ID = os.getenv('APP_ID', "")
    TOKEN = os.getenv('BOT_TOKEN', "")
    assert APP_ID, cl("Please set the APP_ID environment variable.", Colors.RED)
    assert TOKEN, cl("Please set the BOT_TOKEN environment variable.", Colors.RED)

    run(APP_ID, TOKEN)

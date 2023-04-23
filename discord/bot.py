#!/usr/bin/env python3
import asyncio
import os
import sys
from collections import deque
from typing import Dict, List
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

# Load default environment variables (.env)
load_dotenv()

class Monitor(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(
        with_app_command=True,
        help="Starts new instance.",
        brief="Starts new instance.",
        description="Starts new instance.",
        usage="/start instance_name",
        )
    async def start(self, ctx, instance_name: str):
        global start_message
        start_message = await ctx.send(f"Started {instance_name}!")
        await start_message.add_reaction("✅")

    @commands.hybrid_command(with_app_command=True)
    async def finish(self, ctx):
        if start_message:
            await start_message.edit(content="Stopped!")
            await start_message.clear_reaction("✅")

    @commands.hybrid_command(
        with_app_command=True,
        hidden=True,
        )
    async def secret(self,ctx):
        secret_message = await ctx.send(f"Hello, {ctx.author.mention}! This message is only visible to you.", delete_after=30.0)
        await secret_message.add_reaction("❌")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        print(cl('Reaction added:', Colors.YELLOW) + f' {reaction.emoji} by {user.name} on {reaction.message.content}')

        # if reaction.message.author == bot.user and user != bot.user:
        #     if reaction.emoji == "❌":
        #         await reaction.message.delete()

class DiscordBot():
    def __init__(self, app_id: str, token: str):
        self.app_id = app_id
        self.token = token

        self.intents = discord.Intents.all()
        self.intents.members = True
        self.intents.messages = True
        self.intents.reactions = True
        self.intents.message_content = True

        self.bot = commands.Bot(
            application_it=app_id,
            command_prefix='!',
            intents=self.intents
        )

        asyncio.run(self.bot.add_cog(Monitor(self)))

    async def sync(self):
        await self.bot.tree.sync()

    def run(self):
        self.bot.run(self.token)

def run(app_id: str, token: str):
    discordBot = DiscordBot(app_id, token)

    @discordBot.bot.event
    async def on_ready():
        print(cl(f'{discordBot.bot.user}', Colors.GREEN) + ' has connected to Discord!')
        await discordBot.bot.tree.sync()
        print(cl('Tree synced', Colors.CYAN))

    discordBot.run()

if __name__ == "__main__":
    APP_ID = os.getenv('APP_ID', "")
    TOKEN = os.getenv('BOT_TOKEN', "")
    assert APP_ID, cl("Please set the APP_ID environment variable.", Colors.RED)
    assert TOKEN, cl("Please set the BOT_TOKEN environment variable.", Colors.RED)

    run(APP_ID, TOKEN)

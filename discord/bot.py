#!/usr/bin/env python3
import os
import sys
import time
import logging
from collections import deque
from typing import Dict, List
import asyncio
import importlib
import openai
import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
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

class Bot(commands.Bot):
    def __init__(self, app_id: str, token: str, *args, **kwargs):
        intents = discord.Intents.all()
        intents.members = True
        intents.messages = True
        intents.reactions = True
        intents.message_content = True

        self.app_id = app_id
        self.token = token

        super().__init__(application_id=app_id, command_prefix='/', intents=intents)

start_message = None

APP_ID = os.getenv('APP_ID', "")
TOKEN = os.getenv('BOT_TOKEN', "")
assert APP_ID, cl("Please set the APP_ID environment variable.", Colors.RED)
assert TOKEN, cl("Please set the BOT_TOKEN environment variable.", Colors.RED)

bot = Bot(APP_ID, TOKEN)

@bot.hybrid_command(
    with_app_command=True,
    help="Starts new instance.",
    brief="Starts new instance.",
    description="Starts new instance.",
    usage="/start")
async def start(ctx):
    global start_message
    start_message = await ctx.send("Started!")
    await start_message.add_reaction("✅")

@bot.hybrid_command(with_app_command=True)
async def finish(ctx):
    if start_message:
        await start_message.edit(content="Stopped!")
        await start_message.clear_reaction("✅")

@bot.hybrid_command(with_app_command=True)
async def secret(ctx):
    secret_message = await ctx.send(f"Hello, {ctx.author.mention}! This message is only visible to you.", delete_after=30.0)
    await secret_message.add_reaction("❌")

@bot.event
async def on_reaction_add(reaction, user):
    if reaction.message.author == bot.user and user != bot.user:
        if reaction.emoji == "❌":
            await reaction.message.delete()

@bot.event
async def on_ready():
    print(cl(f'{bot.user}', Colors.GREEN) + ' has connected to Discord!')
    await bot.tree.sync()

def run():
    bot.run(bot.token)

if __name__ == "__main__":
    run()

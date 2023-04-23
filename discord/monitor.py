import sys
import asyncio

import discord
import discord.app_commands as app_commands
from discord.ext import commands, tasks

from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from extensions.ray_objectives import CooperativeObjectivesListStorage
from extensions.ray_tasks import CooperativeTaskListStorage

# await ctx.interaction.response.send_message(f"Hello, {ctx.author.mention}!", ephemeral=True)
# secret_message = await ctx.send(f"Hello, {ctx.author.mention}! This message is only visible to you.", delete_after=30.0)
# await secret_message.add_reaction("❌")

class Monitor(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        asyncio.run(bot.add_cog(self))

    async def cog_unload(self):
        await self.fetcher.cancel()

    @commands.hybrid_command(with_app_command=True)
    async def start(self, ctx):
        self.channel = ctx.channel.id
        self.interaction = ctx.interaction
        await ctx.interaction.response.send_message(f"Connecting...", ephemeral=True, silent=True)

        self.objectives_raw = CooperativeObjectivesListStorage()
        if not self.objectives_raw.get_objective_names():
            await self.interaction.followup.send(f"No objectives being worked towards currently", ephemeral=True, silent=True)
            await self.after_fetcher()
            return

        self.start_message_deleted = False

        self.objectives = {}

        self.fetcher.start()

    @commands.hybrid_command(with_app_command=True)
    async def finish(self, ctx):
        self.fetcher.stop()
        await ctx.interaction.response.send_message(f"Disconnecting...", delete_after=1, ephemeral=True, silent=True)

    @tasks.loop(seconds=5.0)
    async def fetcher(self):
        if not self.start_message_deleted:
            start_message = await self.interaction.original_response()
            try:
                await start_message.delete()
            except discord.errors.NotFound:
                pass
            self.start_message_deleted = True

        channel = self.bot.get_channel(self.channel)

        objectives_raw = self.objectives_raw.get_objective_names()
        for name in objectives_raw:
            objective = {'name': name, 'tasks': CooperativeTaskListStorage(name)} if name not in self.objectives else self.objectives[name]
            self.objectives[name] = objective
            message_content = "__**Objective:**__\n" + f"```{objective['name']}```" + "__**Tasks:**__\n"

            task_names = objective['tasks'].get_task_names()
            for task in task_names:
                message_content += f"```{task}```"

            if 'message' not in objective:
                objective['message'] = await channel.send(message_content, silent=True)
            else:
                objective['message'] = await objective['message'].edit(content=message_content)

    @fetcher.after_loop
    async def after_fetcher(self):
        if not self.start_message_deleted:
            start_message = await self.interaction.original_response()
            if start_message:
                await start_message.delete()
        self.interaction = None
        self.channel = None
        self.objectives = None
        self.objectives_raw = None

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if reaction.message.author == self.bot.user and user != self.bot.user:
            if reaction.emoji == "❌":
                await reaction.message.delete()

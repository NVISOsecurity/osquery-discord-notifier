import asyncio
import os
import json
import subprocess

import discord
from discord.ext import commands

from .llm import LLMAssistant
from .logs import OsqueryLogReader


class LogEventBot:

    intents = discord.Intents.default()
    intents.messages = True
    intents.message_content = True
    intents.dm_messages = True

    def __init__(self, logger, osquery_log_reader, llm_assistant):
        self.logger = logger
        self.os_query_log_reader: OsqueryLogReader = osquery_log_reader
        self.llm_assistant: LLMAssistant = llm_assistant
        self.authorized_user_id = int(os.environ["DISCORD_AUTHORIZED_USER_ID"])
        self.bot = commands.Bot(command_prefix="!", intents=self.intents)
        self.event_queue = asyncio.Queue()

        self.bot.add_listener(self.on_ready)
        self.bot.add_listener(self.on_message)
        self.bot.add_command(commands.Command(self.stats))

    def run(self):
        # Start the log monitoring in a separate thread
        asyncio.get_event_loop().run_in_executor(None, self.start_log_monitoring)
        self.bot.run(os.environ["DISCORD_BOT_TOKEN"], reconnect=True)

    def start_log_monitoring(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.log_monitoring_task())

    async def log_monitoring_task(self):
        while True:
            new_events = self.os_query_log_reader.get_recent_log_events()

            if len(new_events) > 0:
                self.logger.info("Processing %s new events", len(new_events))

                for event in new_events:
                    await self.event_queue.put(event)

            await asyncio.sleep(1)

    async def background_tasks(self):
        user = await self.bot.fetch_user(self.authorized_user_id)
        llm_test = self.llm_assistant.llm_test()
        
        await user.send("osquery_discord_notifier.py is now running.")
        await user.send(llm_test)

        while True:
            event = await self.event_queue.get()
            if user:
                try:
                    llm_response = self.llm_assistant.llm_question(
                        json.dumps(event, indent=2)
                    )
            
                    message = (
                        "**"+llm_response.get("event_summary")+"**"
                        + "\n"
                        + llm_response.get("event_details")
                    )

                except Exception:
                    message = (
                        "```"
                        + json.dumps(event, indent=2)
                        + "\n"
                        + "Warning: LLM model failed to respond. Fallback to original event."
                        + "```"
                    )
                
                if len(message) > 2000:
                    message = message[:1900] + "\n\n" + "Warning: Message truncated.```"

                await user.send(message)

            self.event_queue.task_done()

    async def on_ready(self):
        self.bot.loop.create_task(self.background_tasks())
        self.logger.info(
            "Logged in as %s and ready to monitor osquery logs", self.bot.user
        )

    async def on_message(self, message):
        if (
            isinstance(message.channel, discord.DMChannel)
            and message.author.id == self.authorized_user_id
        ):
            print(f"Received DM from {message.author}: {message.content}")

    async def stats(self, ctx, *_):
        user = await self.bot.fetch_user(self.authorized_user_id)
        if user:
            try:
                message = "```"

                uptime_result = subprocess.run(
                    "uptime", shell=True, capture_output=True, text=True, check=True
                )
                message += (
                    "System uptime"
                    + "\n=================\n"
                    + uptime_result.stdout.strip()
                    + "\n\n"
                )

                message += "```"

                await user.send(message)
            except discord.HTTPException as e:
                await ctx.send(f"Failed to send message due to HTTP error: {e}")

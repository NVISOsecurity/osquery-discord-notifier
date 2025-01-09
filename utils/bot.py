import asyncio
import os
import json
import subprocess

import discord
from discord.ext import commands

from .llm import LLMAssistant
from .logs import OsqueryLogReader
from .logs import filter_events


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

        self.bot.add_listener(self.on_ready)
        self.bot.add_listener(self.on_message)

        self.bot.add_command(commands.Command(self.stats))

    def run(self):
        self.bot.run(os.environ["DISCORD_BOT_TOKEN"], reconnect=True)

    async def background_tasks(self):
        first_run = True
        while True:
            user = await self.bot.fetch_user(self.authorized_user_id)

            if first_run:
                await user.send("osquery_discord_notifier.py is now running.")
                first_run = False

            new_events = self.os_query_log_reader.get_recent_log_events()
            filtered_events = filter_events(new_events)

            if len(new_events) > 0:
                self.logger.info("Processing %s new events", len(new_events))

            if len(filtered_events) > 0:
                self.logger.info("Notifying %s filtered events", len(filtered_events))

                for event in filtered_events:
                    if user:

                        try:
                            llm_response = self.llm_assistant.llm_question(
                                json.dumps(event, indent=2)
                            )

                            message = (
                                "```"
                                + llm_response.get("event_summary")
                                + "\n\n"
                                + llm_response.get("event_details")
                                + "\n\n"
                                + "Original event data:"
                                + "\n\n"
                                + json.dumps(event, indent=2)
                                + "```"
                            )

                        except Exception as e: 
                            # If for any reason the LLM model fails to respond, fallback to the original event
                            message = (
                                "```"
                                + json.dumps(event, indent=2)
                                + "\n\n"
                                + "Warning: LLM model failed to respond. Fallback to original event."
                                + "```"
                            )
                        
                        # Truncate message to at most 2000 characters & add a note about truncation
                        if len(message) > 2000:
                            message = message[:1900] + "\n\n" + "Warning: Message truncated.```"

                        await user.send(message)

            await asyncio.sleep(1)

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

                # System uptime
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

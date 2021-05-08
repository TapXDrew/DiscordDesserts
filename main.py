import asyncio
import json
import os
import random
import traceback

import discord
from discord.ext import commands


class DiscordDesserts(commands.AutoShardedBot):
    config = json.load(open(os.getcwd() + '/config/config.json'))

    initial_extensions = [
        "cogs.general",
        "cogs.error"
    ]

    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True  # Needs to be true to access members or member events
        intents.presences = False  # Needs to be true if checking Member.status, Member.activity or Member.activities

        super().__init__(command_prefix=commands.when_mentioned_or(self.get_prefix), case_insensitive=True, intents=intents)

        self.default_prefix = '!'

        self.load_commands()

    def load_commands(self):
        for extension in self.initial_extensions:
            try:
                self.load_extension(extension)
            except Exception:
                print(f"Failed to load extension {extension}.")
                traceback.print_exc()
        self.load_extension("jishaku")

    async def get_prefix(self, message):
        self.default_prefix = self.config['Bot']['Default Prefix']
        return commands.when_mentioned_or(self.default_prefix)(self, message)

    async def on_message(self, message):
        await self.process_commands(message)

    async def status_changer(self):
        """
            Setting `Playing ` status
            await bot.change_presence(activity=discord.Game(name="a game"))

            Setting `Streaming ` status
            await bot.change_presence(activity=discord.Streaming(name="My Stream", url=my_twitch_url))

            Setting `Listening ` status
            await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="a song"))

            Setting `Watching ` status
            await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="a movie"))
        """
        playing = []
        streaming = []
        listening = []
        watching = []
        statuses = playing + streaming + listening + watching

        while True:
            if not self.is_ready():
                continue
            elif self.is_closed():
                return
            else:
                await self.change_presence(activity=random.choice(statuses))
                await asyncio.sleep(self.config['Bot']['StatusTimer'])

    async def on_ready(self):
        print("------------------------------------")
        print("Bot Name: " + self.user.name)
        print("Bot ID: " + str(self.user.id))
        print("Discord Version: " + discord.__version__)
        print("------------------------------------")
        # asyncio.create_task(self.status_changer())

    def run(self):
        super().run(self.config['Bot']['Token'], reconnect=True)


if __name__ == "__main__":
    DD = DiscordDesserts()
    DD.run()

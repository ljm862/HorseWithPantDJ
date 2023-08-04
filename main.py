import discord
import asyncio
from discord.ext import commands
from cogs.music_cog import music_cog

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

def run_bot():
    bot = commands.Bot(command_prefix='+', intents=intents)

    @bot.event
    async def on_ready():
        await bot.add_cog(music_cog(bot))
        print("loaded cogs")

    print("Hello World")

    bot.run("TOKEN")

run_bot()
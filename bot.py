"""Main Bot Start Script
"""
import os

import asyncio
import discord
from discord.ext import commands
from ytdb.yt_player import YoutubeCommands

# Configuration - Hardcoded environment variables
DISCORD_TOKEN = "MTQ0MDcxNjk3MDkwMjQyMTY0OA.GXFmrl.b91Z6Bb8tp2ssjp3nypZ4tJHGgmCHcu8DCJm2I"
ENV = "dev"  # Change to "prod" for production
COMMAND_PREFIX = ["/"]  # Command prefix(es) as a list
COOKIES_DATA = None  # Optional: Set to your cookies.txt content as a string if needed


def main():
    """Main"""
    print("Starting YTDB...")

    # Use hardcoded config values
    token = DISCORD_TOKEN
    env = ENV
    print("environment: {env}".format(env=env))

    command_prefix = COMMAND_PREFIX
    print("command_prefix(es): {command_prefix}".format(command_prefix=command_prefix))

    # Create Intents for bot
    print("Creating intents...")
    intents = discord.Intents.default()
    intents.message_content = True
    
    # Create cookies file if it doesn't exist
    if not os.path.exists("cookies.txt"):
        if COOKIES_DATA is None:
            print("Error: cookies.txt file not found and COOKIES_DATA not set. Will try to run anyway...")
        else:
            print("Creating cookies.txt file...")
            with open("cookies.txt", "w") as f:
                f.write(COOKIES_DATA)
        

    # Create bot
    print("Creating main bot...")
    main_bot = commands.Bot(
        command_prefix=command_prefix,
        intents=intents,
        activity=discord.Game("huh?"),
    )

    @main_bot.event
    async def on_ready():
        """On Ready for bot"""
        print(f"{main_bot.user} has connected to Discord!")

    asyncio.run(main_bot.load_extension("ytdb.yt_player"))
    main_bot.run(token)


if __name__ == "__main__":
    main()

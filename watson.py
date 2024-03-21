# __________                  __             __     ________             .___ 
# \______   \  ____    ____  |  | __  ____ _/  |_  /  _____/   ____    __| _/ 
#  |       _/ /  _ \ _/ ___\ |  |/ /_/ __ \\   __\/   \  ___  /  _ \  / __ |  
#  |    |   \(  <_> )\  \___ |    < \  ___/ |  |  \    \_\  \(  <_> )/ /_/ |  
#  |____|_  / \____/  \___  >|__|_ \ \___  >|__|   \______  / \____/ \____ |  
#         \/              \/      \/     \/               \/              \/  
#
# Discord bot for Sherlock by RocketGod
# https://github.com/RocketGod-git/watson

import json
import logging
import platform
import time
import discord
from discord import Embed
import os
import asyncio


class NoShardResumeFilter(logging.Filter):
    def filter(self, record):
        if 'discord.gateway' in record.name and 'has successfully RESUMED session' in record.msg:
            return False
        return True

discord_gateway_logger = logging.getLogger('discord.gateway')
discord_gateway_logger.addFilter(NoShardResumeFilter())

logging.basicConfig(level=logging.INFO)


def load_config():
    try:
        with open('config.json', 'r') as file:
            return json.load(file)
    except Exception as e:
        logging.error(f"Error loading configuration: {e}")
        return None


async def execute_sherlock(interaction, *args):
    python_interpreter = "python3" if platform.system() == "Linux" else "python"
    username = args[0]
    filename = f"{username}.txt"

    await interaction.followup.send(f"Searching `{username}` for {interaction.user.mention}")

    command = [python_interpreter, "../sherlock/sherlock.py"] + list(args)
    process = await asyncio.create_subprocess_exec(*command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)

    while True:
        output = await process.stdout.readline()
        if not output:
            break
        output = output.decode().strip()
        if output:
            await interaction.channel.send(output)

    _, stderr = await process.communicate()

    if process.returncode != 0:
        await handle_errors(interaction, f"An error occurred: {stderr.decode()}")
        return

    try:
        with open(filename, "rb") as f:
            await interaction.channel.send(file=discord.File(f, filename=filename))
            
    except FileNotFoundError:
        await interaction.channel.send(f"No results found for `{username}`.")

    await interaction.channel.send(f"Finished report on `{username}` for {interaction.user.mention}")


class aclient(discord.Client):
    def __init__(self) -> None:
        super().__init__(intents=discord.Intents.default())
        self.tree = discord.app_commands.CommandTree(self)
        self.activity = discord.Activity(type=discord.ActivityType.watching, name="/sherlock")
        self.discord_message_limit = 2000


async def handle_errors(interaction, error, error_type="Error"):
    error_message = f"{error_type}: {error}"
    logging.error(f"Error for user {interaction.user}: {error_message}")  # Log the error in the terminal
    try:
        if interaction.response.is_done():
            await interaction.followup.send(error_message)
        else:
            await interaction.response.send_message(error_message, ephemeral=True)
    except discord.HTTPException as http_err:
        logging.warning(f"HTTP error while responding to {interaction.user}: {http_err}")
        await interaction.followup.send(error_message)
    except Exception as unexpected_err:
        logging.error(f"Unexpected error while responding to {interaction.user}: {unexpected_err}")
        await interaction.followup.send("An unexpected error occurred. Please try again later.")


def run_discord_bot(token):
    client = aclient()

    @client.event
    async def on_ready():
        await client.tree.sync()

        logging.info(f"Bot {client.user} is ready and running in {len(client.guilds)} servers.")
        for guild in client.guilds:
            # Attempt to fetch the owner as a member of the guild
            try:
                owner = await guild.fetch_member(guild.owner_id)
                owner_name = f"{owner.name}#{owner.discriminator}"
            except Exception as e:
                logging.error(f"Could not fetch owner for guild: {guild.name}, error: {e}")
                owner_name = "Could not fetch owner"
            
            logging.info(f" - {guild.name} (Owner: {owner_name})")

        server_count = len(client.guilds)
        activity_text = f"/sherlock on {server_count} servers"
        await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=activity_text))

        logging.info(f'{client.user} is online.')

    @client.tree.command(name="sherlock", description="Search for a username on social networks using Sherlock")
    async def sherlock(interaction: discord.Interaction, username: str):
        await interaction.response.defer(ephemeral=False)
        
        logging.info(f"User {interaction.user} from {interaction.guild if interaction.guild else 'DM'} executed '/sherlock' with username '{username}'.") 

        args = [username]
        args.append("--nsfw")
        
        formatted_username = username.replace("{", "{%}")
        args[0] = formatted_username

        try:
            await execute_sherlock(interaction, *args)
        except Exception as e:
            await handle_errors(interaction, str(e))


    client.run(token)


if __name__ == "__main__":
    config = load_config()
    run_discord_bot(config.get("discord_bot_token"))

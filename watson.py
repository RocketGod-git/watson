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

    if os.path.exists(filename):
        last_modified_time = os.path.getmtime(filename)
    else:
        last_modified_time = None

    command = [python_interpreter, "../sherlock/sherlock.py"] + list(args)
    process = await asyncio.create_subprocess_exec(*command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        await handle_errors(interaction, f"An error occurred: {stderr.decode()}")
        return

    if filename:
        while last_modified_time == os.path.getmtime(filename):
            time.sleep(1)

class aclient(discord.Client):
    def __init__(self) -> None:
        super().__init__(intents=discord.Intents.default())
        self.tree = discord.app_commands.CommandTree(self)
        self.activity = discord.Activity(type=discord.ActivityType.watching, name="/sherlock")
        self.discord_message_limit = 2000

    async def send_split_messages(self, interaction, message: str, require_response=True):

        if not message.strip():
            logging.warning("Attempted to send an empty message.")
            return

        lines = message.split("\n")
        chunks = []
        current_chunk = ""

        for line in lines:
            if len(current_chunk) + len(line) + 1 > self.discord_message_limit:
                chunks.append(current_chunk)
                current_chunk = line + "\n"
            else:
                current_chunk += line + "\n"

        if current_chunk:
            chunks.append(current_chunk)

        if not chunks:
            logging.warning("No chunks generated from the message.")
            return

        if require_response and not interaction.response.is_done():
            await interaction.response.defer(ephemeral=False)

        try:
            await interaction.followup.send(content=chunks[0], ephemeral=False)
            chunks = chunks[1:]  
        except Exception as e:
            logging.error(f"Failed to send the first chunk via followup. Error: {e}")

        for chunk in chunks:
            try:
                await interaction.channel.send(chunk)
            except Exception as e:
                logging.error(f"Failed to send a message chunk to the channel. Error: {e}")

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
        logging.info(f'{client.user} is online.')

    @client.tree.command(name="sherlock", description="Search for a username on social networks using Sherlock")
    async def sherlock(interaction: discord.Interaction, username: str, similar: bool = False):
        await interaction.response.defer(ephemeral=False)
        
        logging.info(f"User {interaction.user} from {interaction.guild if interaction.guild else 'DM'} executed '/sherlock' with username '{username}' and similar option set to {similar}.") 

        args = [username]
        args.append("--nsfw")
        
        if similar:
            formatted_username = username.replace("{", "{%}")
            args[0] = formatted_username

        try:
            await execute_sherlock(interaction, *args)

            with open(f"{username}.txt", "r") as f:
                output = f.read()
            await client.send_split_messages(interaction, output)
        except Exception as e:
            await handle_errors(interaction, str(e))

    @client.tree.command(name="help", description="Displays a list of available commands.")
    async def help_command(interaction: discord.Interaction):
        
        logging.info(f"User {interaction.user} from {interaction.guild if interaction.guild else 'DM'} executed '/help'.") 

        try:
            embed = discord.Embed(title="Available Commands", description="Here are the commands you can use with this bot:", color=0x3498db)
            embed.add_field(name="🔍 Sherlock Command", value="Search for a username across various social networks using the Sherlock tool.", inline=False)
            sherlock_command_description = (
                "**Usage**:\n"
                "`/sherlock [username]` - Search for a specific username.\n"
                "\n**Options**:\n"
                "`similar` - Check similar usernames by replacing with variations (e.g., '_', '-', '.')"
            )
            embed.add_field(name="Details & Options", value=sherlock_command_description, inline=False)
            await interaction.response.send_message(embed=embed, ephemeral=False)
        except Exception as e:
            await handle_errors(interaction, str(e))

    client.run(token)

if __name__ == "__main__":
    config = load_config()
    run_discord_bot(config.get("discord_bot_token"))

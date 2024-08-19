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
import sys
from io import StringIO
import subprocess

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

async def send_message_with_retry(channel, content, max_retries=3):
    for attempt in range(max_retries):
        try:
            await channel.send(content)
            return
        except discord.errors.Forbidden:
            logging.warning(f"Bot doesn't have permission to send messages in channel {channel.id}")
            return
        except discord.errors.HTTPException as e:
            if attempt == max_retries - 1:
                logging.error(f"Failed to send message after {max_retries} attempts: {e}")
            else:
                await asyncio.sleep(1)

async def run_sherlock_process(args, channel, timeout=300):
    sherlock_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    process = await asyncio.create_subprocess_exec(
        sys.executable, "-m", "sherlock.sherlock", *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=sherlock_dir
    )
    
    try:
        async def read_stream(stream):
            output = []
            while True:
                line = await stream.readline()
                if not line:
                    break
                line = line.decode().strip()
                if line:
                    await channel.send(line)
                    output.append(line)
            return '\n'.join(output)

        stdout_task = asyncio.create_task(read_stream(process.stdout))
        stderr_task = asyncio.create_task(read_stream(process.stderr))
        wait_task = asyncio.create_task(process.wait())

        done, pending = await asyncio.wait(
            [stdout_task, stderr_task, wait_task],
            timeout=timeout,
            return_when=asyncio.ALL_COMPLETED
        )

        for task in pending:
            task.cancel()

        if wait_task not in done:
            process.terminate()
            return "", "Process timed out", -1

        stdout = await stdout_task if stdout_task in done else ""
        stderr = await stderr_task if stderr_task in done else ""
        returncode = await wait_task

        return stdout, stderr, returncode
    except asyncio.TimeoutError:
        process.terminate()
        return "", "Process timed out", -1
    except Exception as e:
        return "", f"An error occurred: {str(e)}", -1

async def send_results_as_messages(interaction, filename):
    try:
        with open(filename, 'r') as f:
            content = f.read()
        
        chunks = [content[i:i+1900] for i in range(0, len(content), 1900)]
        
        for chunk in chunks:
            await interaction.followup.send(f"```\n{chunk}\n```")
    except Exception as e:
        await interaction.followup.send(f"Error sending results as messages: {str(e)}")

async def execute_sherlock(interaction, *args):
    if not args:
        await handle_errors(interaction, "No username provided")
        return

    username = args[0]
    
    sherlock_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    filename = os.path.join(sherlock_dir, f"{username}.txt")
    
    await interaction.followup.send(f"Searching `{username}` for {interaction.user.mention}")

    sherlock_args = [username, '--nsfw', '--output', filename, '--local']

    try:
        stdout, stderr, returncode = await run_sherlock_process(sherlock_args, interaction.channel)
        
        if returncode != 0:
            error_message = f"Sherlock exited with code {returncode}\n"
            if stderr:
                error_message += f"Error output:\n```\n{stderr}\n```"
            await handle_errors(interaction, error_message)
            return

        if stderr:
            await interaction.channel.send(f"Warnings occurred:\n```\n{stderr}\n```")

    except Exception as e:
        await handle_errors(interaction, f"An error occurred while running Sherlock: {str(e)}")
        return

    try:
        if os.path.exists(filename):
            file_size = os.path.getsize(filename)
            if file_size > 8 * 1024 * 1024:
                await interaction.channel.send(f"Results file for `{username}` is too large to upload (Size: {file_size / 1024 / 1024:.2f} MB). Sending results as text messages.")
                await send_results_as_messages(interaction, filename)
            else:
                try:
                    with open(filename, "rb") as f:
                        await interaction.channel.send(file=discord.File(f, filename=os.path.basename(filename)))
                except discord.HTTPException as e:
                    await interaction.channel.send(f"Error uploading results file: {str(e)}. Sending results as text messages.")
                    await send_results_as_messages(interaction, filename)
        else:
            await interaction.channel.send(f"No results file found for `{username}`")
    except Exception as e:
        await handle_errors(interaction, f"An error occurred while processing results: {str(e)}")

    await interaction.channel.send(f"Finished report on `{username}` for {interaction.user.mention}")

class aclient(discord.Client):
    def __init__(self) -> None:
        super().__init__(intents=discord.Intents.default())
        self.tree = discord.app_commands.CommandTree(self)
        self.activity = discord.Activity(type=discord.ActivityType.watching, name="/sherlock")
        self.discord_message_limit = 2000

async def handle_errors(interaction, error, error_type="Error"):
    error_message = f"{error_type}: {error}"
    logging.error(f"Error for user {interaction.user}: {error_message}")
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
    active_searches = {}

    @client.event
    async def on_ready():
        await client.tree.sync()

        logging.info(f"Bot {client.user} is ready and running in {len(client.guilds)} servers.")
        for guild in client.guilds:
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

        formatted_username = username.replace("{", "{%}")

        try:
            task = asyncio.create_task(execute_sherlock(interaction, formatted_username))
            active_searches[username] = task
            await task
        except Exception as e:
            await handle_errors(interaction, str(e))
        finally:
            if username in active_searches:
                del active_searches[username]
                

    client.run(token)

if __name__ == "__main__":
    config = load_config()
    run_discord_bot(config.get("discord_bot_token"))

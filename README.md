# Watson - A Discord Bot for Sherlock

Watson is a Discord bot designed to interface with the [Sherlock project](https://github.com/sherlock-project/sherlock). It allows users to search for usernames on various social networks directly from Discord using the power of Sherlock.

## Setup

### Prerequisites

This bot requires the Sherlock project to function. If you haven't already cloned the Sherlock repository, you can do so with the following command:

```bash
git clone https://github.com/sherlock-project/sherlock
```

### Installation

1. Navigate to the `sherlock` directory:

```bash
cd sherlock
```

2. Create a new directory named `discordbot`:

```bash
mkdir discordbot
```

3. Navigate to the `discordbot` directory:

```bash
cd discordbot
```

4. Clone the Watson repository into the `discordbot` directory:

```bash
git clone https://github.com/RocketGod-git/watson .
```

5. Update the `config.json` file with your bot's token. Your `config.json` should look like this:

```json
{
	"discord_bot_token": "REPLACE WITH YOUR BOT TOKEN"
}
```

### Running the Bot

For **Windows** users:

- Run the `run.bat` file. This will automatically set up a virtual environment, install the required packages on the first run, and then run the bot.

- Execute the `run.sh` script:

```bash
./run.bat
```

For **Linux** users:

- Execute the `run.sh` script:

```bash
./run.sh
```

This script will perform the same setup actions as the Windows batch file.

## Usage

Once the bot is running, you can utilize the following slash commands on your Discord server:

### `/sherlock`

Search for a username across various social networks using the Sherlock tool. By default, the search will include NSFW links.

**Usage**:

- `/sherlock [username]`: Search for a specific username.
- **Options**:
  - `similar`: Check for similar usernames by replacing them with variations (e.g., '_', '-', '.').

### `/help`

Displays a list of available commands and their descriptions.

---

Thank you for using Watson! If you find any issues or have any feedback, feel free to contribute to the [Watson repository](https://github.com/RocketGod-git/watson).

![RocketGod](https://github.com/RocketGod-git/shell-access-discord-bot/assets/57732082/c68635fa-b89d-4f74-a1cb-5b5351c22c98)

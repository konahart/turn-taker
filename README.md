# Setup

1. Run the following to install dependencies:
   `pip install -r requirements.txt`

1. Create a Discord token (see [Creating a discord bot & getting a token](https://discordpy.readthedocs.io/en/latest/discord.html))

1. Open the `creds-default.py` file, and replace 'YOUR TOKEN HERE' with your Discord Token. Rename the file to `creds.py`

## Optional: Load games from Google sheets

For added flexibility, Turn Taker can also load game data from Google sheets that are in the [Story Synth Shuffled format](https://docs.storysynth.org/guide/formats.html#shuffled). In order to do so, additional credentials are required.

1. Follow steps 1 through 5 from gspread for [setting up a Service Account for a bot](https://gspread.readthedocs.io/en/latest/oauth2.html#for-bots-using-service-account)

1. Create a file called `creds.json` in the `bot` folder, and place the credentials information there (note: **not** the location suggested by gspread)

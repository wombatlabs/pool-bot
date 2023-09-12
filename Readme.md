test This is the crypto api bot.
The bot is written in python 3.5.


# Installation

sudo apt-get install python3-pip

For easy installation and isolation from the other projects, we suggest to use a python virtualenv.

## Create a virtualenv

> virtualenv .venv -p python3.5

## Activate the virtualenv

> . .venv/bin/activate

## Install the dependencies 

> pip install -r requirements.txt

## Create a telegram bot

- Connect to telegram, 
- Speak to the BotFather and 
- create a bot
- Take note of the bot token. You will need it during the configuration


## Create and configure the channel

- Create a channel on telegram.
- Add the bot to the channel
- Make the bot admin of the channel

## Update the configuration file

Edit the config.py file and update :

- API_TOKEN : enter here the API token you got from the bot father
- ACTIVATE_MODERATOR_FILTERING : set it to True or False if you want the bot to speak with only admins.
- MODERATOR_USER_NAMES : enter in here the usernames of the people that can talk to the bot
- CHANNEL_USERNAME : @enter in here the username of the channel. Do not forget the @ sign
- COIN2URL_MAP : check that your coins are in here with the respective api endpoints

## Start the bot

> python ./crypto_api_bot.py

## Usage 



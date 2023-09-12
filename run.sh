#!/bin/bash
screen -X -S bot kill
source .venv/bin/activate
screen -dmS bot -t BOT-ETC python crypto_api_bot.py

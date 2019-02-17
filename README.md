# MTGCubeTalkBot

A bot for various automation and support in the MTG Cube Talk discord

## About the bot:

This bot is written using the [Discord.py Rewrite](https://github.com/Rapptz/discord.py/tree/rewrite).

The initial intention is to be able to quickly generate Pack 1 Pick 1 screenshots for discussion and theory crafting. Further iterations may have more functionality as desired.

## Requirements

This bot needs [Selenium Hub](https://www.seleniumhq.org/) to function properly and utilizes selenium-python to interact with it. The remainder can be installed with: `pip install -r requirements.txt` and ran in your choice of environment. Docker is not a pre-requisite, but a docker build file is included for convenience and for my deployment purposes. 

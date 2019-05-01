from discord.ext import commands
import asyncio
import os
import logging
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
logger = logging.getLogger('cubebot.main')

#EnvironmentLoaders
botToken = os.environ['CUBEBOT']

#Initializing bot
description = '''CubeBot Commands'''
bot = commands.Bot(command_prefix='-', description=description, pm_help=True)

@bot.event
async def on_ready():
    logger.info('Logged in as')
    logger.info(bot.user.name)
    logger.info(bot.user.id)
    logger.info('------')


bot.load_extension("functions.rotisserie")

bot.run(botToken)

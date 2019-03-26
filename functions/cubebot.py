from functions import cubetutor
import logging
import discord
import sys
import asyncio
import random
import requests
from discord.ext import commands

#shahrazad token ed98810941cf53fa9806f9aa9299c2 - This is only available internally and only executes the shahrazad test pipeline
logger = logging.getLogger('cubebot.cubebot')

logger.info("cubebot cog loaded")

class Application(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command(pass_context=True)
	async def p1p1(self, ctx):
		"""Generate a P1P1 image given a cubetutor cube ID"""
		command = ctx.message.content.split()
		if len(command) > 1:
			try:
				cubeId = int(command[1])
				logger.info(str(ctx.message.author) + " pulled a pack")
				await ctx.channel.send("Looking up pack...")
				cubeId = command[1]
				packLoader = self.bot.loop.create_task(cubetutor.CubeTutorPackChrome(cubeId, ctx))
			except:
				await ctx.channel.send("Please give me a real ID at least. ")
		if len(command) is 1:
			await ctx.channel.send("I need an ID.")

def setup(bot):
	bot.add_cog(Application(bot))

from functions import cubetutor
from datetime import datetime, timedelta
from random import random, shuffle
import logging
import discord
import sys
import asyncio
import random
import requests
import os
import json
from discord.ext import commands

logger = logging.getLogger('cubebot.rotisserie')

logger.info("rotisserie cog loaded")

cubeObjects = []
for fil in os.listdir("./cubes/"):
    if fil.startswith("json-"):
        with open("./cubes/"+fil, "r") as jsonFile:
            cubeObjects.append(json.load(jsonFile))
        logger.info("Appending parsed list " + fil)

async def saveCubes():
    while True:
        if cubeObjects:
            for cube in cubeObjects:
                with open("./cubes/json-"+str(cube["name"]), "w+") as jsonFile:
                     json.dump(cube, jsonFile)
            logger.info("Saving cube")
        await asyncio.sleep(10)

async def updateServer(bot):
    await bot.wait_until_ready()
    while True:
        logger.info("Updating server")
        if cubeObjects:
            for cube in cubeObjects:
                logger.info(cube["name"])
                channel = bot.get_channel(cube["name"])
                logger.info(channel)
                embed = discord.Embed(title="Draft Pick Board (try `$help rot` and `$rot rules`)", description=cube["link"], color=0x00ff00)
                for player in cube["players"]:
                    playerName = bot.get_user(player["player"])
                    turnNum = cube["players"].index(player)
                    if (turnNum != 0 and len(cube["players"][turnNum-1]["picks"]) > len(cube["players"][turnNum]["picks"]) \
                          or (turnNum == 0 \
                            and len(cube["players"][turnNum-1]["picks"]) == len(cube["players"][turnNum]["picks"]))):
                        embed.set_footer(text="Active Drafter: " + playerName.name + " | Cards selected so far: " + str(len(player["picks"])) + " of 45")
                    pickList = "```\n"
                    for pick in player["picks"]:
                        pickList += str(pick) + "\n"
                    embed.add_field(name=playerName.name, value=pickList + "```")
                origMessage = await channel.get_message(cube["message"])
                await origMessage.edit(embed=embed)
        await asyncio.sleep(10)

class Application(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(saveCubes())
        self.bot.loop.create_task(updateServer(self.bot))

    @commands.Cog.listener()
    async def on_message(self, message):
        """Make sure non bot messages are deleted"""
        if message.author != self.bot.user and not message.content.startswith("$rot"):
            try:
                await message.delete()
            except Exception as e:
                logger.info(e)
    
    @commands.group()
    async def rot(self, ctx):
        logger.info(ctx.message.author.name + "\t" + str(ctx.message.content))
        """Group for managing a Rotisserie style draft"""
        if not ctx.invoked_subcommand:
            await ctx.message.delete()
        return

    @rot.command()
    async def rules(self, ctx):
        """Display rules of the Rotisserie draft"""
        message = """
        See $help rot to see the command help specifics.
        All messages in this channel will be deleted after they're typed
        $rot join to join the festivities
        $rot pick (your selection), best to copy/paste if possible but must be exact

        Good luck!
        """
        embed = discord.Embed(title = "Rules of the draft", description = message)
        await ctx.message.author.send(embed=embed)
        await ctx.message.delete()
        return

    @rot.command()
    async def start(self, ctx):
        """All members joined, start the draft!"""
        for cube in cubeObjects:
            if cube["name"] == ctx.channel.id:
                if not cube["ready"]:
                    cube["ready"] = True
                    shuffle(cube["players"])
                    embed = discord.Embed(title="Draft Pick Board", description=cube["link"], color=0x00ff00)
                    for player in cube["players"]:
                        playerName = self.bot.get_user(player["player"])
                        embed.add_field(name=playerName.name, value="empty")
                    origMessage = await ctx.send(embed=embed)
                    cube["message"] = origMessage.id
        await ctx.message.delete()
         

    @rot.command()
    async def create(self, ctx, link):
        """Attach newline delimited list of cube, $rot create http://cubetutor.com/viewcube/<id>"""
        for cube in cubeObjects:
            if cube["name"] == ctx.channel.id:
                await ctx.author.send("The game has already been created.")
                await ctx.message.delete()
                return
        rawPath = "./cubes/raw-"+str(ctx.channel.id)
        await ctx.message.attachments[0].save(rawPath)
        logger.info("downloaded new cube for channel: " + str(ctx.channel.id))
        cubeList = []
        with open(rawPath, "r") as cubeListRaw:
             cubeListParsed = cubeListRaw.readlines()
             for card in cubeListParsed:
                 cubeList.append(card.lower().rstrip())
        logger.info(str(len(cubeList)) + " cards loaded")
        cube = {"name": ctx.channel.id, "list": cubeList, "players": [], "ready": False, "link": link, "message": None}
        cubeObjects.append(cube)
        os.remove(rawPath)
        logger.info(str(cube["name"]) + " loaded")
        await ctx.message.delete()

    @rot.command()
    async def delete(self, ctx):
        """End a draft"""
        for cube in cubeObjects:
            if cube["name"] == ctx.channel.id:
                cubeObjects.remove(cube)
                os.remove("./cubes/json-"+str(ctx.channel.id))
        await ctx.message.delete()

    @rot.command()
    async def pick(self, ctx, *, card):
        """Make your selection"""
        for cube in cubeObjects:
            if cube["name"] == ctx.channel.id:
                if not cube["ready"]:
                    await ctx.message.author.send("Games not ready yet!")
                    await ctx.message.delete()
                    return
                for player in cube["players"]:
                    if ctx.author.id == player["player"]:
                        turnNum = cube["players"].index(player)
                        if (turnNum != 0 and len(cube["players"][turnNum-1]["picks"]) == len(cube["players"][turnNum]["picks"]) \
                          or (turnNum == 0 \
                            and len(cube["players"][turnNum-1]["picks"]) < len(cube["players"][turnNum]["picks"]))):
                            await ctx.message.author.send("It's not your turn!")
                            await ctx.message.delete()
                            return
                        if card.lower() in cube["list"]:
                            player["picks"].append(card.lower())
                            cube["list"].remove(card.lower())
                            player["rb"] = False
                            await ctx.message.delete()
                            stopDrafting = False
                            for player in cube["players"]:
                                if len(player["picks"]) == 45:
                                    stopDrafting = True
                                if len(player["picks"]) < 45:
                                    stopDrafting = False
                            if stopDrafting:
                                cube["ready"] = False
                                await ctx.send("Drafting is completed! All choices are final and locked.")
                            return
                        await ctx.message.author.send("Wasn't able to add the card, sorry. Likely the card is already taken; probably by Ruben")
                        await ctx.message.delete()
                        return
                await ctx.message.author.send("Doesn't look like you're in the game yet, try $rot join")
                await ctx.message.delete()
        await ctx.message.delete()
    
  #  @rot.command(aliases=["fuck"])
  #  async def undo(self, ctx):
  #      """Undo your selection"""
  #      for cube in cubeObjects:
  #          if cube["name"] == ctx.channel.id:
  #              for player in cube["players"]:
  #                  if (turnNum != 0 and len(cube["players"][turnNum-1]["picks"]) == len(cube["players"][turnNum]["picks"]) \
  #                    or (turnNum == 0 \
  #                      and len(cube["players"][turnNum-1]["picks"]) < len(cube["players"][turnNum]["picks"]))):
  #                      await ctx.message.author.send("It's not your turn!")
  #                      return
  #                  if player["player"] == ctx.author.id and not player["rb"]:
  #                      cube["list"].append(player["picks"][-1])
  #                      del player["picks"][-1] 
  #                      player["rb"] = True

    @rot.command()
    async def dl(self, ctx):
        """Download your current picks in line delimited format (for tapped out)"""
        return
        await ctx.message.delete()

    @rot.command()
    async def join(self, ctx):
        """Join an active game"""
        for cube in cubeObjects:
            if cube["name"] == ctx.channel.id:
                if cube["ready"]:
                    await ctx.author.send("Game is already started, you can't join!")
                    return
                found = False
                for player in cube["players"]:
                    if ctx.author.id == player["player"]:
                        found = True
                if not found:
                    cube["players"].append({"player": ctx.author.id, "picks": [], "rb": False})
                    logger.info(str(cube))
            else:
                logger.info("No active games found")
        await ctx.message.delete()

    @rot.command()
    async def leave(self, ctx):
        """Leave the draft, you can't come back!"""
        for cube in cubeObjects:
            if cube["name"] == ctx.channel.id:
                for player in cube["players"]:
                    if ctx.author.id == player["player"]:
                        for card in player["picks"]:
                            cube["list"].append(card)
                        cube["players"].remove(player)
        await ctx.message.delete()

def setup(bot):
    bot.add_cog(Application(bot))

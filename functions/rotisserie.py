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

#Load cubes on init
cubeObjects = []
for fil in os.listdir("./cubes/"):
    if fil.startswith("json-"):
        with open("./cubes/"+fil, "r") as jsonFile:
            cubeObjects.append(json.load(jsonFile))
        logger.info("Appending parsed list " + fil)

async def saveCubes():
    if cubeObjects:
        for cube in cubeObjects:
            with open("./cubes/json-"+str(cube["name"]), "w+") as jsonFile:
                 json.dump(cube, jsonFile)
        logger.info("Saving cube")

async def updateServer(bot, ctx):
    logger.info("Updating server")
    if cubeObjects:
        for cube in cubeObjects:
            if cube["name"] != ctx.channel.id:
                continue
            logger.info(cube["name"])
            #Get the channel from the context of the command
            channel = ctx.message.channel
            logger.info(channel)
            embed = discord.Embed(title="Game Master: " + bot.get_user(cube["creator"]).name + " - Draft Pick Board (try `$help rot` and `$rot rules`)", description=cube["link"], color=0x00ff00)
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
            await saveCubes()
            try:
                #Find the original message and server to update
                origMessage = await channel.fetch_message(cube["message"])
                await origMessage.edit(embed=embed)
            except Exception as e:
                logger.info(e)

class Application(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        """Make sure non bot messages are deleted"""
        if message.author != self.bot.user and not message.content.startswith("$rot") and "rotisserie" in message.channel.name:
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
            if cube["name"] == ctx.channel.id and cube["creator"] == ctx.author.id:
                if not cube["ready"]:
                    cube["ready"] = True
                    shuffle(cube["players"])
                    embed = discord.Embed(title="Draft Pick Board", description=cube["link"], color=0x00ff00)
                    for player in cube["players"]:
                        playerName = self.bot.get_user(player["player"])
                        embed.add_field(name=playerName.name, value="empty")
                    origMessage = await ctx.send(embed=embed)
                    cube["message"] = origMessage.id
        await updateServer(self.bot, ctx)
        await ctx.message.delete()
         

    @rot.command()
    async def create(self, ctx, link=None):
        """Attach newline delimited list of cube, `$rot create <link to view the cube list> (ADD THE FILE!)`"""
        if "rotisserie" not in str(ctx.message.channel.name):
            await ctx.author.send("You can only create a rotisserie draft in a room with `rotisserie` in the name")
            return
        if len(ctx.message.attachments) == 0:
            await ctx.author.send("You must attach a newline delimited list of cube cards to pick from")
            await ctx.message.delete()
            return
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
        cube = {"creator": ctx.author.id, "name": ctx.channel.id, "list": cubeList, "players": [{"player": ctx.author.id, "picks": []}], "ready": False, "link": link, "message": None}
        await ctx.channel.edit(topic="Players: " + ctx.message.author.name)
        cubeObjects.append(cube)
        os.remove(rawPath)
        logger.info(str(cube["name"]) + " loaded")
        await updateServer(self.bot, ctx)
        async for message in ctx.channel.history():
            await message.delete()

    @rot.command()
    async def removeDraft(self, ctx):
        """End a draft"""
        for cube in cubeObjects:
            if cube["name"] == ctx.channel.id and cube["creator"] == ctx.message.author.id:
                cubeObjects.remove(cube)
                os.remove("./cubes/json-"+str(ctx.channel.id))
                await ctx.channel.edit(topic="No drafts active.")
        await updateServer(self.bot, ctx)
        await ctx.message.delete()

    @rot.command()
    async def cleanRoom(self, ctx):
        for cube in cubeObjects:
            if cube["name"] == ctx.channel.id and cube["creator"] == ctx.message.author.id:
                async for message in ctx.channel.history():
                    if message.id == cube["message"]:
                        continue
                    await message.delete()
                await updateServer(self.bot, ctx)

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
                            lastPlayer = False
                            if turnNum == len(cube["players"])-1:
                                lastPlayer = True
                                cube["players"].reverse()
                            await updateServer(self.bot, ctx)
                            await ctx.message.delete()
                            stopDrafting = False
                            for player in cube["players"]:
                                if len(player["picks"]) == 2:
                                    stopDrafting = True
                                if len(player["picks"]) < 2:
                                    stopDrafting = False
                            if not stopDrafting:
                                if not lastPlayer:
                                    await self.bot.get_user(cube["players"][turnNum+1]["player"]).send("It's your turn!")
                                if lastPlayer:
                                    await self.bot.get_user(cube["players"][0]["player"]).send("It's still your turn!")
                                return
                            if stopDrafting:
                                for cube in cubeObjects:
                                    if cube["name"] == ctx.channel.id:
                                        embed = discord.Embed(title="Picks from the draft: ", description=ctx.channel.guild.name + " - " + ctx.channel.name)
                                        for player in cube["players"]:
                                            picks = "```\n"
                                            for pick in player["picks"]:
                                                picks += pick + "\n"
                                            embed.add_field(name=self.bot.get_user(player["player"]).name, value=picks+"```") 
                                        for player in cube["players"]:
                                            await self.bot.get_user(player["player"]).send(embed=embed)
                                        cubeObjects.remove(cube)
                                        os.remove("./cubes/json-"+str(ctx.channel.id))
                                        await updateServer(self.bot, ctx)
                                await ctx.channel.edit(topic="No drafts active. ", reason="Draft completed.")
                                await ctx.send("Drafting is completed! All choices are final and locked.")
                                await ctx.message.delete()
                                return
                        await ctx.message.author.send("Wasn't able to add the card, sorry. Likely the card is already taken.")
                        await ctx.message.delete()
                        return
                await ctx.message.author.send("Doesn't look like you're in the game yet, try $rot join")
                await ctx.message.delete()
                return
    
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
                    cube["players"].append({"player": ctx.author.id, "picks": []})
                    topic = "Players: "
                    for player in cube["players"]:
                        topic = topic + str(self.bot.get_user(player["player"]).name) + " | "
                    await ctx.channel.edit(topic=topic, reason="New player joined.")
                    logger.info(str(cube))
            else:
                logger.info("No active games found")
        await updateServer(self.bot, ctx)
        await ctx.message.delete()

    @rot.command()
    async def leave(self, ctx):
        """Leave the draft, you can't come back!"""
        for cube in cubeObjects:
            if cube["name"] == ctx.channel.id:
                topic = "Players: "
                for player in cube["players"]:
                    if ctx.author.id == player["player"]:
                        for card in player["picks"]:
                            cube["list"].append(card)
                        cube["players"].remove(player)
                    if ctx.author.id != player["player"]:
                        topic = topic + str(self.bot.get_user(player["player"]).name) + " | "
                await ctx.channel.edit(topic=topic, reason="Player left the game.")
                await ctx.message.author.send("You have successfully left the draft.")
                if len(cube["players"]) == 0:
                    for cube in cubeObjects:
                        if cube["name"] == ctx.channel.id:
                            cubeObjects.remove(cube)
                            os.remove("./cubes/json-"+str(ctx.channel.id))
                    await ctx.channel.edit(topic="No drafts active. ", reason="Last active player left, game deleted.")
                    await ctx.message.delete()
                    return
                if cube["creator"] == ctx.author.id:
                    cube["creator"] = cube["players"][0]["player"]
        await updateServer(self.bot, ctx)
        await ctx.message.delete()

    @rot.command()
    async def kick(self, ctx):
        """Kick @players from a draft, they can't come back!"""
        for cube in cubeObjects:
            if cube["name"] == ctx.channel.id and cube["creator"] != ctx.author.id:
                await ctx.message.author.send("You're not the GM, you can't kick people!")
                await self.bot.get_user(cube["creator"]).send(ctx.message.author.name + " just tried to kick someone from a draft! Rude.\n" + "```"+ctx.message.clean_content+"```")
                await ctx.message.delete()
                return
            if cube["name"] == ctx.channel.id and cube["creator"] == ctx.author.id:
                newOwnerNeeded = False
                for member in ctx.message.mentions:
                    await member.send("You've been kicked from the " + ctx.guild.name + " rotisserie draft by " + str(ctx.author))
                    if member.id == cube["creator"]:
                        newOwnerNeeded = True
                    for player in cube["players"]:
                        if member.id == player["player"]:
                            for card in player["picks"]:
                                cube["list"].append(card)
                            cube["players"].remove(player)
                            if len(cube["players"]) == 0:
                                for cube in cubeObjects:
                                    if cube["name"] == ctx.channel.id:
                                        cubeObjects.remove(cube)
                                        os.remove("./cubes/json-"+str(ctx.channel.id))
                                await ctx.channel.edit(topic="No drafts active. ", reason="No active players left, game deleted.")
                if len(cube["players"]) == 0:
                    topic = "No drafts active. "
                if len(cube["players"]) > 0:
                    topic = "Players: "
                    for player in cube["players"]:
                        topic = topic + str(self.bot.get_user(player["player"]).name) + " | "
                    await ctx.channel.edit(topic=topic, reason="Player(s) were kicked from the game. ")     
                    if newOwnerNeeded:
                        cube["creator"] = cube["players"][0]["player"]
        await updateServer(self.bot, ctx)    
        await ctx.message.delete()

def setup(bot):
    bot.add_cog(Application(bot))

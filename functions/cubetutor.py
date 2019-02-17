from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import os
import discord

selenium = os.environ["HUB"]

async def CubeTutorPackChrome(cubeId, ctx):
    try:
        cubeId = int(cubeId)
    except Exception as e:
        print(e)
        return False
    endpoint = "http://www.cubetutor.com/samplepack/"+str(cubeId)
    driver = webdriver.Remote(
        command_executor = selenium + "wd/hub",
        desired_capabilities = {"browserName": "chrome", "javascriptEnabled": True}
        )
    try:
        driver.get(endpoint)
    except Exception as e:
        print(e)
        await tearDownClass(driver)
        
    try:
        gtfo = webdriver.common.action_chains.ActionChains(driver)
        footer = driver.find_element_by_id('footer')
        gtfo.move_to_element(footer)
        element = driver.find_element_by_id('main')
        elementPng = element.screenshot_as_png
        
        await tearDownClass(driver, png=elementPng, ctx=ctx)
    except Exception as e:
        print(e)
        await tearDownClass(driver)

async def tearDownClass(driver, png=None, ctx=None): 
    driver.quit()
    if png:
        packImage = discord.File(png, "crack.png")
        await ctx.channel.send("You're pack, friend. ", file=packImage)
    if not png:
        await ctx.channel.send("Sorry, your pack couldn't be found. Please try again later.")

if __name__ == "__main__":
    setUpClass()
    

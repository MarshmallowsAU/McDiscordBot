import json
import os
import subprocess
import asyncio

# https://github.com/Uncaught-Exceptions/MCRcon
from mcrcon import MCRcon

# https://docs.disnake.dev/en/stable/
import disnake
from disnake.ext import commands


# Variable setup
running = False
envVarsFile = open("realVariables.json")
envVars = json.load(envVarsFile)
bot = commands.Bot(sync_commands_debug=True)
bot.run(envVars["botToken"])

# Wrapper to mcrcon
def controller(cmd):
    # Connect remotely to the server
    mcrcon = MCRcon(envVars["serverAddr"],
                    envVars["rconPass"],
                    port=envVars["rconPort"])
    try:
        mcrcon.connect()
        response = mcrcon.command(cmd)
        mcrcon.disconnect()
        return response
    
    except Exception as error:
        print(error)
        return "Something went fucky wucky, consult @marshmallows_ or try again in a minute"
        

# Starts the server
#   Usage: Will be called once the bot is pinged with the command, break is called if the server is killed
async def run():
    global running
    running = True

    webhook_send("Starting Server")
    # Runs the server start command through the shell
    process = await asyncio.create_subprocess_shell(envVars["startScript"],
                                                    stderr=asyncio.subprocess.PIPE)
    
    while True:
        err = await process.stdout.realine()

        if err:
            break
    
    running = False
    webhook_send("Server Shut Down")


# Automatically closes the server if no players are online at any given point
#   Usage: Uses remote controller to check if players are online, else calls for a shutdown
#   Timing: Check occurs every 5 minutes after server start
#
# NOTE: Don't make it do this I wanna save on my electrical bill
async def autoshutdown():
    while running:
        asyncio.sleep(300)
        controller("execute unless entity @a run stop")


# Webhook setup for Discord Bot to send messages
async def webhook_send(content):
    channelid = envVars["chatChannelId"]
    channel = bot.get_channel(int(channelid))
    exist = False
    webhooks = await channel.webhooks()
    for webhook in webhooks:
        if webhook.name == "BotChatWebhook":
            exist = True
    if not exist:
        await channel.create_webhook(name="BotChatWebhook")
    for webhook in webhooks:
        try:
            await webhook.send(str(content), avatar_url="https://img.freepik.com/premium-vector/marshmallow-cartoon-marshmallow-character-design_21085-1016.jpg")
        except Exception:
            pass

# Keeps the bot in a ready state
@bot.event
async def on_ready():
    print("Logged in as {0.user}".format(bot))
    await bot.change_presence(activity=disnake.Game("/help for help"))

# Starts the server (duh)
@bot.slash_command(description="Starts the server")
async def start(inter):
    await inter.response.defer()
    if running:
        await inter.edit_original_message(content="Server is already running! ")
    else:
        asyncio.create_task(run())
        asyncio.create_task(autoshutdown())
        await inter.edit_original_message(content="Started server. ")

# Attempts to shut down the server, only succeeds if no players are online
@bot.slash_command(description="Stops the server")
async def stop(inter):
    await inter.response.defer()
    if running:
        print("Attempting manual shutdown... ")
        try:
            await inter.edit_original_message(content=controller("execute unless entity @a run stop"))
        except Exception:
            await inter.edit_original_message(content="Could not stop the server. ")
    else:
        await inter.edit_original_message(content="Server is already down. ")

# Takes in command args from the discord channel to be used
@bot.event
async def on_message(message):
    if message.author.bot:
        return  
    if str(message.channel.id) not in envVars["chatChannelId"]:
        return
    await message.delete()
    if not controller("list").startswith("There are"):
        msg = await message.channel.send("Server is not running. ")
        await asyncio.sleep(5)
        await msg.delete()
        return
    try:
        msg = await message.channel.send(controller('tellraw @a ["{'+str(await bot.fetch_user(message.author.id))+'} '+message.content+'"]'))
        await asyncio.sleep(5)
        await msg.delete()
        return
    except disnake.errors.HTTPException:
        pass
    await webhook_send(message.content)
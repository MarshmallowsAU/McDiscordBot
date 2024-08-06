import json
import asyncio

# https://github.com/Uncaught-Exceptions/MCRcon
from mcrcon import MCRcon

# https://docs.disnake.dev/en/stable/
import disnake
from disnake.ext import commands


# Variable setup
running = False
envVarsFile = open("McDiscordBot/realVariables.json")
envVars = json.load(envVarsFile)
bot = commands.Bot(sync_commands_debug=True)

# Wrapper to mcrcon
def controller(cmd):
    # Connect remotely to the serverear
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
        print("Server Stopped")

# Starts the server
#   Usage: Will be called once the bot is pinged with the command, break is called if the server is killed
async def run():
    global running
    running = True

    print("Server started. ")
    proc = await asyncio.create_subprocess_shell(envVars["startScript"],stdout=asyncio.subprocess.PIPE) 
    while True: 
        data = await proc.stdout.readline()
        if not data:
            break
        line = data.decode('latin1').rstrip()
        print(line)
    running = False
    print("Server stopped. ")

# Automatically closes the server if no players are online at any given point
#   Usage: Uses remote controller to check if players are online, else calls for a shutdown
#   Timing: Check occurs every 5 minutes after server start
#
# NOTE: Don't make it do this I wanna save on my electrical bill
async def autoshutdown():
    await asyncio.sleep(300)
    while running:
        print("Starting No Player Checks")
        await asyncio.sleep(60)
        controller("execute unless entity @a run stop")

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
        except disnake.errors.HTTPException:
            await inter.edit_original_message(content="Could not stop the server. ")
    else:
        await inter.edit_original_message(content="Server is already down. ")

# Attempts to shut down the server, only succeeds if no players are online
@bot.slash_command(description="Shows IP Address and Port")
async def server_info(inter):
    await inter.response.defer()
    try:
        await inter.edit_original_message(content="IP Address = " + envVars["serverAddr"] + "\nPort = " + envVars["serverPort"])
    except disnake.errors.HTTPException:
        await inter.edit_original_message(content="Could not stop the server. ")

bot.run(envVars["botToken"])

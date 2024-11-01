#for env file
import os
from dotenv import load_dotenv

#to connect to mongodb 
from pymongo import MongoClient

#main discord libraries needed
import discord
from discord.ext import commands
from discord import app_commands

#get the token from env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = os.getenv('DISCORD_GUILD')
MONGO_URL = os.getenv('MONGO_URL')

#connect to mongoDB
mongo = MongoClient(MONGO_URL)
# Specify the database and collection
db = mongo["Discord_Info"]
user_commands_collection = db["User Commands"]
print("Connected to MongoDB!")

#saves a personal command for the user and uploads it to mongodb
#parameters: user_id (int) -the user's Discord ID
#            command_name (str) - name of the command 
#            command_data (str) - text that the command would output 
#No output
async def save_user_command(user_id, command_name, command_data):
    user_commands_collection.update_one(
        {"user_id": user_id},
        {"$set": {command_name: command_data}},
        upsert=True
    )
    print(f"Command '{command_name}' saved for user {user_id}.")

#retrieves a command from a user's personal collection
#parameters: user_id (int) -the user's Discord ID
#            command_name (str) - name of the command 
#returns: the text associated with the command 
async def get_user_command(user_id, command_name):
    user_data = user_commands_collection.find_one({"user_id": user_id})
    if user_data:
        return user_data.get(command_name)
    else:
        return None


#set up intents
intents = discord.Intents.default()
intents.message_content = True
#set up discord connection
client = commands.Bot(command_prefix="#", intents=intents)
GUILD_NUM = discord.Object(id = GUILD_ID)

@client.event
async def on_ready():
    #sync commands with Guild
    try:
        synced = await client.tree.sync(guild = GUILD_NUM)
        print(f"Synced {len(synced)} commands to guild {GUILD_NUM.id}")
    except Exception as e:
        print(f"Error syncing commands: {e}")
        
    print(f'{client.user} has connected to Discord!')

# @client.event
# async def on_message(message):
#     # print(str(message.author))
#     username = str(message.author).split("#")[0]
#     channel = str(message.channel.name)
#     user_message = str(message.content)
    
#     #check if message was from this bot
#     if message.author == client.user:
#         return
    
#     print(f"User {username} wrote in {channel}: {user_message}")
    
#     if user_message == "hello":
#         await message.channel.send(f"Hello there {username}")

@client.tree.command(name = "hello_there", description = "Replys with Hello There", guild = GUILD_NUM)
async def sayHello(interaction : discord.Integration):
    await interaction.response.send_message("Hello There")

@client.tree.command(name = "repeat", description = "Replys with Hello There", guild = GUILD_NUM)
async def repeatPhrase(interaction : discord.Integration, print_out : str):
    await interaction.response.send_message(print_out)

@client.tree.command(name = "save_cmd", description = "Saves a text command for the user", guild = GUILD_NUM)
async def saveCmd(interaction : discord.Integration, cmd_name : str, text_output : str):
    await save_user_command(interaction.user.id, cmd_name, text_output)
    await interaction.response.send_message(f"Command {cmd_name} saved")

@client.tree.command(name = "get_cmd", description = "Retrieves a text command for the user and outputs it", guild = GUILD_NUM)
async def saveCmd(interaction : discord.Integration, cmd_name : str):
    phrase = await get_user_command(interaction.user.id, cmd_name)
    await interaction.response.send_message(phrase)

#TODO 

client.run(TOKEN)
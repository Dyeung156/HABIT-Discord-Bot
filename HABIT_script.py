import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

#get the token from env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = os.getenv('DISCORD_GUILD')

#set up intents
intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix="#", intents=intents)



@client.event
async def on_ready():
    try:
        guild = discord.Object(id = GUILD_ID)
        synced = await client.tree.sync(guild = guild)
        print(f"Synced {len(synced)} commands to guild {guild.id}")
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

GUILD_NUM = discord.Object(id = GUILD_ID)
@client.tree.command(name = "hello_there", description = "Replys with Hello There", guild = GUILD_NUM)
async def sayHello(interaction : discord.Integration):
    await interaction.response.send_message("Hello There")

@client.tree.command(name = "repeat", description = "Replys with Hello There", guild = GUILD_NUM)
async def sayHello(interaction : discord.Integration, print_out : str):
    await interaction.response.send_message(print_out)
    
    
#TODO 

client.run(TOKEN)
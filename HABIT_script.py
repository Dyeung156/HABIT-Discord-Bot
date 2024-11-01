import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

#get the token from env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

#set up intents
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
client = commands.Bot(command_prefix="#")

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

@client.event
async def on_message(message):
    username = str(message.author).split("#")[0]
    channel = str(message.channel.name)
    user_message = str(message.content)
    
    #check if message was from this bot
    if message.author == client.user:
        return
    
    print(f"User {username} wrote in {channel}: {user_message}")
    
    if user_message == "hello":
        await message.channel.send(f"Hello there {username}")
        
@client.command()
async def ping(ctx):
    await ctx.send("Pong")

#TODO 
#Set up Git respo for this dumb dumb
client.run(TOKEN)
#for env file
import os
from dotenv import load_dotenv

#import Database functions 
from Model import save_user_command, get_user_command, get_all_user_commands, delete_command
#import View
import View

#main discord libraries needed
import discord
from discord.ext import commands

#for message history 
from datetime import datetime

#get the token from env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = os.getenv('DISCORD_GUILD')

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

@client.tree.command(name = "main_menu", description = "Calls the main menu", guild = GUILD_NUM)
async def send_main_menu(interaction: discord.Interaction):
    await interaction.response.send_message("", view = View.MainMenu())  # Send a message with the View

@client.tree.command(name = "cmd_menu", description = "Calls the menu for user commands", guild = GUILD_NUM)
async def send_cmd_menu(interaction: discord.Interaction):
    cmd_selections = await get_all_user_commands(interaction.user.id)
    await interaction.response.send_message("", view = View.CmdMenu(cmd_selections, "get"))  # Send a message with the View

@client.tree.command(name = "delete_menu", description = "Calls the menu to delete a command", guild = GUILD_NUM)
async def send_cmd_menu(interaction: discord.Interaction):
    cmd_selections = await get_all_user_commands(interaction.user.id)
    await interaction.response.send_message("", view = View.CmdMenu(cmd_selections, "delete"))  # Send a message with the View

@client.tree.command(name = "save_cmd", description = "Saves a text command for the user", guild = GUILD_NUM)
async def saveCmd(interaction : discord.Interaction, cmd_name : str, text_output : str):
    await save_user_command(interaction.user.id, cmd_name, text_output)
    await interaction.response.send_message(f"Command {cmd_name} saved", ephemeral = True)

@client.tree.command(name = "get_cmd", description = "Retrieves a text command for the user and outputs it", guild = GUILD_NUM)
async def getCmd(interaction : discord.Interaction, cmd_name : str):
    try:
        phrase = await get_user_command(interaction.user.id, cmd_name)
        if phrase is None:
            phrase = f"Command {cmd_name} not found"
        await interaction.response.send_message(phrase)
        
    except discord.errors.InteractionResponded:
        # Prevent additional response attempts if already responded
        print("Interaction has already been responded to.")
        
@client.tree.command(name = "delete_cmd", description = "Deletes a command for the user", guild = GUILD_NUM)
async def deleteACmd(interaction: discord.Interaction, cmd_name : str):
    result = await delete_command(interaction.user.id, cmd_name)
    await interaction.response.send_message(f"Command {cmd_name} deleted: {result}", ephemeral = True)

@client.tree.command(name = "search_history_phrases", description = "Look at the top (count) messages you repeated the most after a certain date", guild = GUILD_NUM)
async def searchHistory(interaction : discord.Interaction, count: int, date : str = None):
    try:
        # Parse the 'after' date if provided
        after_date = datetime.strptime(date, "%Y-%m-%d") if date else None
    except ValueError:
        await interaction.response.send_message("Invalid date format. Please use YYYY-MM-DD.", ephemeral=True)
        return
    
    user = interaction.user
    messages = await View.find_top_messages(interaction, user, count, after_date)
    print(messages)
    if messages:
        response = "\n".join([f"Used {msg[1]} times: {msg[0]}" for msg in messages])
        add_on = f" after {date}" if date else ""
        await interaction.response.send_message(f"Last {count} messages from {user.mention}{add_on}:\n{response}")
    else:
         await interaction.response.send_message("User has not sent any messages.", ephemeral = True)
    
client.run(TOKEN)
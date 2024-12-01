#for env file
import os
from dotenv import load_dotenv

#to connect to mongodb 
# from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient

#main discord libraries needed
import discord
from discord.ext import commands

import asyncio

#get the token from env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = os.getenv('DISCORD_GUILD')
MONGO_URL = os.getenv('MONGO_URL')

#connect to mongoDB
mongo = AsyncIOMotorClient(MONGO_URL)
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
    user_data = await user_commands_collection.find_one({"user_id": user_id})
    if user_data:
        return user_data.get(command_name)
    else:
        return None

#get all commands from a user's personal collection
async def get_all_user_commands(user_id):
    user_data = await user_commands_collection.find_one({"user_id": user_id})  
    if user_data:
        # Remove 'user_id' key to return only the commands in a dict format
        return {key for key, value in user_data.items() if key != "user_id" and key != "_id"}
    else:
        return None

#set up intents
intents = discord.Intents.default()
intents.message_content = True
#set up discord connection
client = commands.Bot(command_prefix="#", intents=intents)
GUILD_NUM = discord.Object(id = GUILD_ID)

class MainMenu(discord.ui.View): 
    @discord.ui.select( # the decorator that lets you specify the properties of the select menu
        placeholder = "Choose an action", # the placeholder text that will be displayed if nothing is selected
        min_values = 1, # the minimum number of values that must be selected by the users
        max_values = 1, # the maximum number of values that can be selected by the users
        options = [ # the list of options from which users can choose, a required field
            discord.SelectOption(
                label="Save Command",
                description="Create a personal command and upload it", 
                value = "save_cmd"
            ),
            discord.SelectOption(
                label="Get Command",
                description="Retrieve a personal command and have HABIT send in chat",
                value = "get_cmd"
            ),
        ]
    )
    async def select_callback(self, interaction : discord.Interaction, select : discord.ui.select):
        action = select.values[0]
        # await interaction.response.send_message(f"Executing {action}", ephemeral = True)
        
        if action == "get_cmd":
            cmd_selections = await get_all_user_commands(interaction.user.id)
            await interaction.response.edit_message(content = "", view = CmdMenu(cmd_selections)) 
        elif action == "save_cmd":
            await interaction.response.send_modal(ModalForCmd())


class ModalForCmd(discord.ui.Modal):
    def __init__(self):
        super().__init__(title = "Form to Save a Command")
        
        # Add the form for the command name 
        self.cmd_name_form = discord.ui.TextInput(
            label = "Command Name",
            placeholder = "Enter a name for the command",
            required = True
        )
        self.add_item(self.cmd_name_form)

        # Add the form for the command output 
        self.cmd_output_form = discord.ui.TextInput(
            label = "Command Output",
            placeholder = "Enter output for the command",
            required = True
        )
        self.add_item(self.cmd_output_form)
        
    async def on_submit(self, interaction: discord.Interaction):
        cmd_name = self.cmd_name_form.value
        cmd_output = self.cmd_output_form.value
        
        await save_user_command(interaction.user.id, cmd_name, cmd_output)
        await interaction.response.send_message(f"Command {cmd_name} saved", ephemeral = True)
        
class CmdMenu(discord.ui.View):
    #init the menu with a set of the user's commands 
    def __init__(self, cmd_selections):
        super().__init__()
        
        select_options = [
            discord.SelectOption(label=label, value=label)
            for label in cmd_selections
        ]
        
        select = discord.ui.Select(
            placeholder="Choose an action",
            min_values=1,
            max_values=1,
            options=select_options
        )
        select.callback = self.cmd_menu_callback
        self.add_item(select)
    
    async def cmd_menu_callback(self, interaction : discord.Interaction):
        action = interaction.data["values"][0]

        # await interaction.response.send_message(f"Executing {action}", ephemeral = True)
        
        # Handle the action, e.g., execute a specific command
        phrase = await get_user_command(interaction.user.id, action)
        if phrase is None:
            phrase = f"Command {action} not found"
        await interaction.response.send_message(phrase)
        
        #using the slash command's callback will get 2 responses to the same interaction
        #will need to see if this can be fixed. Copy-pasting otherwise for now
        
        # if await getCmd.callback(interaction, action):
        #     print(f"Executed {action}")
        # else:
        #     print(f"Failed to execute {action}")
        
    @discord.ui.button(label="", row = 1, style=discord.ButtonStyle.primary, emoji="⬅️") 
    async def return_to_main(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content = "", view = MainMenu()) 

@client.tree.command(name = "main_menu", description = "Calls the main menu", guild = GUILD_NUM)
async def send_main_menu(interaction: discord.Interaction):
    await interaction.response.send_message("", view = MainMenu())  # Send a message with the View

@client.tree.command(name = "cmd_menu", description = "Calls the menu for user commands", guild = GUILD_NUM)
async def send_cmd_menu(interaction: discord.Interaction):
    cmd_selections = await get_all_user_commands(interaction.user.id)
    
    await interaction.response.send_message("", view = CmdMenu(cmd_selections))  # Send a message with the View

@client.event
async def on_ready():
    #sync commands with Guild
    try:
        synced = await client.tree.sync(guild = GUILD_NUM)
        print(f"Synced {len(synced)} commands to guild {GUILD_NUM.id}")
    except Exception as e:
        print(f"Error syncing commands: {e}")
    
    print(f'{client.user} has connected to Discord!')

@client.tree.command(name = "repeat", description = "Replys with Hello There", guild = GUILD_NUM)
async def repeatPhrase(interaction : discord.Interaction, print_out : str):
    await interaction.response.send_message(print_out)

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
        
@client.tree.command(name = "get_all_cmd", description = "Retrieves all commands for the user and outputs it", guild = GUILD_NUM)
async def getAllCmd(interaction : discord.Interaction):
    phrase = await get_all_user_commands(interaction.user.id)
    
    if phrase == None:
        phrase = f"Commands not found"

    await interaction.response.send_message(phrase)

client.run(TOKEN)
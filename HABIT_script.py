#for env file
import os
from dotenv import load_dotenv

#to connect to mongodb 
from pymongo import MongoClient

#main discord libraries needed
import discord
from discord.ext import commands

#import commands from other py files
import commands_files.menu_commands
import asyncio

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

#get all commands from a user's personal collection
async def get_all_user_commands(user_id):
    user_data = await user_commands_collection.find_one({"user_id": user_id})  
    if user_data:
        # Remove 'user_id' key to return only the commands in a dict format
        return {key: value for key, value in user_data.items() if key != "user_id" and key != "_id"}
    else:
        return None

#set up intents
intents = discord.Intents.default()
intents.message_content = True
#set up discord connection
client = commands.Bot(command_prefix="#", intents=intents)
GUILD_NUM = discord.Object(id = GUILD_ID)

class MyView(discord.ui.View): # Create a class called MyView that subclasses discord.ui.View
    @discord.ui.select( # the decorator that lets you specify the properties of the select menu
        placeholder = "Choose an action", # the placeholder text that will be displayed if nothing is selected
        min_values = 1, # the minimum number of values that must be selected by the users
        max_values = 1, # the maximum number of values that can be selected by the users
        options = [ # the list of options from which users can choose, a required field
            discord.SelectOption(
                label="Save Command",
                description="Pick this if you like vanilla!", 
                value = "save_cmd"
            ),
            discord.SelectOption(
                label="Get Command",
                description="Pick this if you like chocolate!",
                value = "get_cmd"
            ),
        ]
    )
    async def select_callback(self, interaction : discord.Interaction, select : discord.ui.select):
        action = select.values[0]
        await interaction.response.send_message(f"Executing {action}", ephemeral = True)
        
        def check(message):
            return message.author == interaction.user and message.channel == interaction.channel

        try:
            message = await interaction.client.wait_for("message", timeout=30.0, check=check)
            if action == "save_cmd":
                # Programmatically call the `command1` slash command
                await saveCmd.callback(interaction, input_text=message.content)
            elif action == "get_cmd":
                # Programmatically call the `command2` slash command
                await getCmd.callback(interaction, input_text=message.content)
        except asyncio.TimeoutError:
            await interaction.followup.send("You didn't provide input in time. Try again!")
 
        
    @discord.ui.button(label="", row = 1, style=discord.ButtonStyle.primary, emoji="⬅️") 
    async def button_call(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("You clicked the button!") 
        
    @discord.ui.button(label="", row = 1, style=discord.ButtonStyle.primary, emoji="➡️") 
    async def button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("You clicked the button!") # Send a message when the button is clicked

@client.tree.command(name = "menu", description = "Calls the menu for user commands", guild = GUILD_NUM)
async def button(interaction: discord.Interaction):
    await interaction.response.send_message("", view=MyView())  # Send a message with the View

@client.event
async def on_ready():
    #sync commands with Guild
    try:
        synced = await client.tree.sync(guild = GUILD_NUM)
        print(f"Synced {len(synced)} commands to guild {GUILD_NUM.id}")
    except Exception as e:
        print(f"Error syncing commands: {e}")
    
    print(f'{client.user} has connected to Discord!')

@client.tree.command(name = "hello_there", description = "Replys with Hello There", guild = GUILD_NUM)
async def sayHello(interaction : discord.Interaction):
    await interaction.response.send_message("Hello There")

@client.tree.command(name = "repeat", description = "Replys with Hello There", guild = GUILD_NUM)
async def repeatPhrase(interaction : discord.Interaction, print_out : str):
    await interaction.response.send_message(print_out)

@client.tree.command(name = "save_cmd", description = "Saves a text command for the user", guild = GUILD_NUM)
async def saveCmd(interaction : discord.Interaction, cmd_name : str, text_output : str):
    await save_user_command(interaction.user.id, cmd_name, text_output)
    await interaction.response.send_message(f"Command {cmd_name} saved", ephemeral = True)

@client.tree.command(name = "get_cmd", description = "Retrieves a text command for the user and outputs it", guild = GUILD_NUM)
async def getCmd(interaction : discord.Interaction, cmd_name : str):
    phrase = await get_user_command(interaction.user.id, cmd_name)
    
    if phrase == None:
        phrase = f"Command {cmd_name} not found"
    await interaction.response.send_message(phrase)

@client.tree.command(name = "get_all_cmd", description = "Retrieves all commands for the user and outputs it", guild = GUILD_NUM)
async def getCmd(interaction : discord.Interaction):
    phrase = get_all_user_commands(interaction.user.id)
    
    if phrase == None:
        phrase = f"Commands not found"
    print(phrase)

client.run(TOKEN)
#for env file
import os
from dotenv import load_dotenv

#to connect to mongodb 
# from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient

#main discord libraries needed
import discord
from discord.ext import commands

#for message history 
from datetime import datetime

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
async def save_user_command(user_id, command_name, command_output):
    # filter by user id
    filter = {"user_id": user_id}  
    
    # Find the user's current command list
    user_data = await user_commands_collection.find_one(filter)
    
    # Check if the command already exists in the user's document
    if user_data and command_name in user_data.get("commands", {}):
        # If the command already exists, do nothing (ignore it)
        return
    
    # Define the update operation so that it only inserts if command doesn't exist 
    update = {
        "$set": {
            f"commands.{command_name}": {
                "command_output": command_output,
                "occurrences": 0
            }
        }
    }
    
    # Update the document
    user_commands_collection.update_one(filter, update, upsert=True)  # upsert=True will create the document if it doesn't exist

#increment a command by 1
#parameters: user_id (int) -the user's Discord ID
#            command_name (str) - name of the command 
#no output
async def increment_occurance(user_id, command_name):
    # Filter by user_id
    filter = {"user_id": user_id}
    
    # Define the update operation to increment occurrences
    update = {
        "$inc": {f"commands.{command_name}.occurrences": 1}
    }
    
    # Update the document
    result = await user_commands_collection.update_one(filter, update)

#retrieves a command from a user's personal collection
#parameters: user_id (int) -the user's Discord ID
#            command_name (str) - name of the command 
#returns: the text associated with the command 
async def get_user_command(user_id, command_name):
    #get the document for the user's collection
    user_data = await user_commands_collection.find_one({"user_id": user_id})
    # Check if user data exists and the command exists in the 'commands' dictionary
    if user_data and command_name in user_data.get("commands", {}):
        await increment_occurance(user_id, command_name)
        return user_data["commands"][command_name]["command_output"]
    else:
        return None  # Return None if the command doesn't exist or the user is not found

#get all commands from a user's personal collection
#parameters: user_id (int) - the user's Discord ID
#returns: a list of all command names with that user ID
async def get_all_user_commands(user_id):
    user_data = await user_commands_collection.find_one({"user_id": user_id})  
    
    if user_data:
        commands = [(key, value["occurrences"]) for key, value in user_data["commands"].items()]
        commands = sorted(commands, key = lambda x : x[1], reverse = True)
        return [name for name , num in commands]
        
    else:
        return []

#delete a command from a user's persoanl collection
#parameters: user_id (int) -the user's Discord ID
#            command_name (str) - name of the command 
#returns: boolean detailing if anything was deleted
async def delete_command(user_id, command_name):
    # Define the filter to find the user by user_id
    filter = {"user_id": user_id}
    
    # Define the update operation to remove the specific command from the 'commands' dictionary
    update = {"$unset": {f"commands.{command_name}": ""}}
    
    # Update the document to remove the command
    result = await user_commands_collection.update_one(filter, update)
    
    # if modified_count > 0, then something was deleted
    return result.modified_count > 0

#finds the top messages that a user has sent in the channel
#parameters: interaction (discord.interaction) - the discord interaction the user made
#            user (discord.user) - the discord user this function is looking at 
#            count (int) - number of messages function should return
#            date (str)(optional) - date messages should be after 
#returns: results (list) - sorted list of tuples (message content, number of occurances)
async def find_top_messages(interaction : discord.Interaction, user : discord.user, count: int, date : str = None):
# Create the dictionary to hold messages
    message_dict = dict()
    
    num_msg = 0
    # Fetch all messages in the channel after date and organize by first letter
    async for message in interaction.channel.history(limit=None, after=date):  
        if message.author == user:
            
            if message.content in message_dict:
                message_dict[message.content] += 1
            else:
                message_dict[message.content] = 1
                
            num_msg += 1
            #hard limit to avoid too much sorting
            if num_msg == 1000: 
                break
    
    # sort the dict and then get the top items with the highest values
    results = sorted(message_dict.items(), key=lambda item: item[1], reverse=True)[:count]
    return results

#set up intents
intents = discord.Intents.default()
intents.message_content = True
#set up discord connection
client = commands.Bot(command_prefix="#", intents=intents)
GUILD_NUM = discord.Object(id = GUILD_ID)

class MainMenu(discord.ui.View): 
    @discord.ui.select( 
        placeholder = "Main Menu Action", 
        min_values = 1, 
        max_values = 1, 
        options = [ 
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
            discord.SelectOption(
                label="Delete Command",
                description="Delete a personal command",
                value = "delete_cmd"
            ),
            discord.SelectOption(
                label="Top Message History Command",
                description="See most repeated messages. Can save a message as a command by selecting it",
                value = "history_cmd"
            ),
        ]
    )
    async def select_callback(self, interaction : discord.Interaction, select : discord.ui.select):
        action = select.values[0]
        # await interaction.response.send_message(f"Executing {action}", ephemeral = True)
        
        if action == "get_cmd":
            cmd_selections = await get_all_user_commands(interaction.user.id)
            await interaction.response.edit_message(content = "", view = CmdMenu(cmd_selections, "get")) 
        elif action == "save_cmd":
            await interaction.response.send_modal(ModalForCmd())
        elif action == "delete_cmd":
            cmd_selections = await get_all_user_commands(interaction.user.id)
            await interaction.response.edit_message(content = "", view = CmdMenu(cmd_selections, "delete")) 
        elif action == "history_cmd":
            cmd_selections = await find_top_messages(interaction, interaction.user, 10, None)
            await interaction.response.edit_message(content = "", view = HistoryMenu(cmd_selections)) 
        
class ModalForCmd(discord.ui.Modal):
    def __init__(self, cmd_name : str = None):
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
            default = cmd_name,
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
    def __init__(self, cmd_selections, usage):
        super().__init__()
        
        #check if any commands are in the list first
        if len(cmd_selections) == 0:
            select_options = [discord.SelectOption(label = "No commands found", value = "No cmds")]
        else:
            select_options = [
                discord.SelectOption(label=label, value=label)
                for label in cmd_selections
            ]
            
        
        select = discord.ui.Select(
            placeholder = "Command Menu" if usage == "get" else "Delete Command",
            min_values=1,
            max_values=1,
            options=select_options
        )
        
        #attach proper callback
        if len(cmd_selections) == 0:
            select.callback = error_message
        elif usage == "get":
            select.callback = cmd_menu_callback
        elif usage == "delete":
            select.callback = delete_menu_callback
            
        self.add_item(select)
        
    @discord.ui.button(label="", row = 1, style=discord.ButtonStyle.primary, emoji="⬅️") 
    async def return_to_main(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content = "", view = MainMenu()) 

async def error_message(interaction: discord.Interaction):
    await interaction.response.send_message("Please save a command first.", ephemeral = True)

async def cmd_menu_callback(interaction : discord.Interaction):
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

async def delete_menu_callback(interaction : discord.Interaction):
    cmd_name = interaction.data["values"][0]

    # await interaction.response.send_message(f"Executing {action}", ephemeral = True)
    
    # delete the command and record the result
    result = await delete_command(interaction.user.id, cmd_name)
    #send feedback to the user
    await interaction.response.send_message(f"Command {cmd_name} deleted: {result}", ephemeral = True)

class HistoryMenu(discord.ui.View):
    def __init__(self, message_history):
        super().__init__()
        
        #check if any messages are in the list first
        if len(message_history) == 0:
            select_options = [discord.SelectOption(label = "No messages found", value = "No messages")]
        else:
            select_options = [
                discord.SelectOption(label = f"Used {num} times: {label}", value=label)
                for label , num in message_history
            ]
            
        select = discord.ui.Select(
            placeholder = "Click on message to save it as a command",
            min_values=1,
            max_values=1,
            options=select_options
        )
        
        #attach proper callback
        if len(message_history) == 0:
            select.callback = history_error
        else:
            select.callback = history_selection
        
        self.add_item(select)
        
    @discord.ui.button(label="", row = 1, style=discord.ButtonStyle.primary, emoji="⬅️") 
    async def return_to_main(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content = "", view = MainMenu()) 

async def history_error(interaction : discord.Interaction):
    await interaction.response.send_message("Please save a command first.", ephemeral = True)

async def history_selection(interaction: discord.Interaction):
    cmd_name = interaction.data["values"][0]
    await interaction.response.send_modal(ModalForCmd(cmd_name))

@client.tree.command(name = "main_menu", description = "Calls the main menu", guild = GUILD_NUM)
async def send_main_menu(interaction: discord.Interaction):
    await interaction.response.send_message("", view = MainMenu())  # Send a message with the View

@client.tree.command(name = "cmd_menu", description = "Calls the menu for user commands", guild = GUILD_NUM)
async def send_cmd_menu(interaction: discord.Interaction):
    cmd_selections = await get_all_user_commands(interaction.user.id)
    
    await interaction.response.send_message("", view = CmdMenu(cmd_selections, "get"))  # Send a message with the View

@client.tree.command(name = "delete_menu", description = "Calls the menu to delete a command", guild = GUILD_NUM)
async def send_cmd_menu(interaction: discord.Interaction):
    cmd_selections = await get_all_user_commands(interaction.user.id)
    
    await interaction.response.send_message("", view = CmdMenu(cmd_selections, "delete"))  # Send a message with the View

@client.event
async def on_ready():
    #sync commands with Guild
    try:
        synced = await client.tree.sync(guild = GUILD_NUM)
        print(f"Synced {len(synced)} commands to guild {GUILD_NUM.id}")
    except Exception as e:
        print(f"Error syncing commands: {e}")
    
    print(f'{client.user} has connected to Discord!')

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
    messages = await find_top_messages(interaction, user, count, after_date)
    print(messages)
    if messages:
        response = "\n".join([f"Used {msg[1]} times: {msg[0]}" for msg in messages])
        add_on = f" after {date}" if date else ""
        await interaction.response.send_message(f"Last {count} messages from {user.mention}{add_on}:\n{response}")
    else:
         await interaction.response.send_message("User has not sent any messages.", ephemeral = True)
    

client.run(TOKEN)
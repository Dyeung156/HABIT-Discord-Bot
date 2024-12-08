import discord
from Model import save_user_command, get_user_command, get_all_user_commands, delete_command

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
    await interaction.response.send_message("Please discuss in the channel more for longer message history", ephemeral = True)

async def history_selection(interaction: discord.Interaction):
    cmd_name = interaction.data["values"][0]
    await interaction.response.send_modal(ModalForCmd(cmd_name))

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
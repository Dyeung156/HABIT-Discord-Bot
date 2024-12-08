#for env file
import os
from dotenv import load_dotenv

#to connect to mongodb 
# from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient

#get the token from env file
load_dotenv()
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


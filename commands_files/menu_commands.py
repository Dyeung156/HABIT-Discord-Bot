import discord

class MyView(discord.ui.View): # Create a class called MyView that subclasses discord.ui.View
    @discord.ui.button(label="Click me!", style=discord.ButtonStyle.primary, emoji="😎") # Create a button with the label "😎 Click me!" with color Blurple
    async def button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("You clicked the button!") # Send a message when the button is clicked

@discord.app_commands.command(name="testing_button", description="A button for testing.")
async def test_button(interaction: discord.Interaction):
    """A slash command that displays a button."""
    await interaction.response.send_message("This is a button!", view=MyView())  # Send a message with the View
    
async def setup(bot):
    bot.tree.add_command(test_button)
    
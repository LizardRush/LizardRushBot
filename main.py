import discord
import os
import aiohttp
import asyncio
import json
import requests
from github import Github, GithubException
from discord import app_commands
from dotenv import load_dotenv

def print_positive(text):
    print(f"\033[32m[+] {text}\033[0m")

def print_negative(text):
    print(f"\033[31m[-] {text}\033[0m")

def print_neutral(text):
    print(f"\033[35m[*] {text}\033[0m")

# Load environment variables
load_dotenv("./.env")

async def fetch_json(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            content = await response.text()
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                print(f"Failed to decode JSON. Content: {content}")
                return None

lizardbot_data = fetch_json("https://raw.githubusercontent.com/LizardRush/LizardRushBot/refs/heads/main/config.json")

# Environment variables
DISCORD_TOKEN = os.getenv("TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB")

# Constants
handle = "https://raw.githubusercontent.com/LizardRush/LizardRushBot/main/"
prefix = '!'
doors_prefix = "#"
hidden_command_channels = []
voice_client = None

# Initialize Discord Client
client = discord.Client(intents=discord.Intents.all())
tree = app_commands.CommandTree(client)
owner_id = 1056032871841792110
owner = None  # Initialize owner to None

# Fetch JSON data

# Send DM to owner
async def dm_owner(message):
    global owner  # Use the global owner variable
    if owner is None:
        owner = await client.fetch_user(lizardbot_data["owner_ID"])
    await owner.send(message)

async def command_output(out):
    channel = await client.fetch_channel(lizardbot_data["command_output_channel"])
    await channel.send(out)

# Convert dictionary to permission overwrite
def dict_to_permission_overwrite(permissions):
    return discord.PermissionOverwrite(
        allow=discord.Permissions(permissions["allow"]),
        deny=discord.Permissions(permissions["deny"])
    )

# Post file to GitHub
def post_file_to_github(repo_name, file_path, file_content, commit_message, token=GITHUB_TOKEN):
    g = Github(token)
    try:
        repo = g.get_repo(repo_name)
        try:
            contents = repo.get_contents(file_path)
            repo.update_file(file_path, commit_message, file_content, contents.sha)
            print(f"Updated '{file_path}' in repo '{repo_name}'.")
        except GithubException as e:
            if e.status == 404:
                repo.create_file(file_path, commit_message, file_content)
                print(f"Created '{file_path}' in repo '{repo_name}'.")
            else:
                print(f"Error handling file: {e}")
    except GithubException as e:
        print(f"Error accessing repo '{repo_name}': {e}")

def is_file_in_repo(repo_name, file_path):
    link = f"https://raw.githubusercontent.com/{repo_name}/{file_path}"
    if requests.get(link).status_code == 200:
        return link
    else:
        return False

# Create an embed message
def create_embed(title, description, color=0x000000):
    embed = discord.Embed(title=title, description=description, color=color)
    return embed

# Send a message as a specific user
async def say_as(channel, identity, avatar_url, message):
    webhook = await channel.create_webhook(name=identity)
    await webhook.send(content=message, username=identity, avatar_url=avatar_url)
    await webhook.delete()

# Generate user stats
import json
import os

async def generate_stats(user, ctx=None):
    if not user.bot:
        file_path = f"./stats/{user.id}.json"
        try:
            # Properly create and initialize the JSON file
            with open(file_path, "w") as file:
                json_data = {
                    "Name": user.name,
                    "ID": user.id,
                    "Can_Restore": False,
                    "Coins": 0,
                    "Warnings": 0,
                }
                file.write(json.dumps(json_data, indent=4))

            if ctx:
                await ctx.send(f'Created stats for {user.display_name}')
            print_positive(f'Created stats for {user.display_name}')
        except Exception as e:
            print_negative(f"Error creating stats: {e}")
            if ctx:
                await ctx.send(f'Failed to create stats for {user.display_name}')
    else:
        if ctx:
            await ctx.send(f'User is a bot: {user.display_name}')
        print_neutral(f'User is a bot: {user.display_name}')


# Get user stats
async def get_stats(user):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{handle}/stats/{user.id}_stats.json") as response:
            if response.status == 200:
                return await response.json()
            elif response.status == 404:
                await generate_stats(user, None)
                return {
                    "Name": user.name,
                    "ID": user.id,
                    "Coins": 0,
                    "Warnings": 0,
                }

@client.event
async def on_ready():
    os.system("clear")
    await setup_hook()
    print_neutral(f"Bot is ready and connected as {client.user}")

    if client.ws is not None:
        await client.change_presence(status=discord.Status.dnd)
    else:
        print("WebSocket connection is not established.")

    for member in client.get_guild(1197655423621267516).members:
        await generate_stats(member)

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if client.user in message.mentions:
        await message.reply("hi.")

@client.event
async def on_guild_join(guild):
    # Check if the bot has joined the specific guild
    if guild.id == 1259668377090265088:
        # Send DM to every member in the server
        for member in guild.members:
            if not member.bot:  # Don't DM bots
                try:
                    await member.send("Hello and bye")
                except discord.Forbidden:
                    print_neutral(f"Could not DM {member.name}. They might have DMs disabled.")
        
        # Leave the guild after sending the messages
        await guild.leave()
        print_positive(f"Left the guild: {guild.name} (ID: {guild.id}) after sending DMs.")


# Setup hook for command tree
async def setup_hook():
    try:
        await tree.sync()
        print_positive("Synced commannds!")
    except Exception as e:
        print_negative(f"Error syncing command tree: {e}")

@tree.command(name="give_coins", description="Give a user some coins")
@app_commands.describe(user="The person to give them to", amount="Coins amount")
async def give_coins(interaction: discord.Interaction, user: discord.User, amount: int):
    if interaction.user.guild_permissions.administrator:
        try:
            data = await get_stats(user)
            data["Coins"] += amount
            with open(f"./stats/{user.id}.json", "w") as file:
                file.write(json.dumps(data, indent=4))
            await interaction.response.send_message(f"Gave {amount} coins to {user.name}", ephemeral=True)
            print_positive(f"Gave {amount} coins to {user.name}")
        except Exception as e:
            print_negative(f"Cannot give coins: {e}")
    else:
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)


@tree.command(name="warn", description="Warn a user, if they get warned after they get 3 warnings they get banned")
@app_commands.describe(user="The person to warn")
async def warn(interaction: discord.Interaction, user: discord.User):
    data = await get_stats(user)
    if interaction.user.guild_permissions.administrator and not user.guild_permissions.administrator:
        try:
            if data['Warnings'] >= 3:
                await interaction.response.send_message(f'{user.display_name} has been banned for 3 warnings.', ephemeral=True)
                await user.ban(reason='3 warnings')
            else:
                data['Warnings'] += 1
                with open(f"./stats/{user.id}.json", "w") as file:
                    file.write(json.dumps(data, indent=4))
                await interaction.response.send_message(f"Warned {user.display_name}", ephemeral=True)
            print_positive(f"Warned {user.display_name}")
        except Exception as e:
            print_negative(f"Error warning: {e}")
    else:
        await interaction.response.send_message("You cannot warn that user", ephemeral=True)

@tree.command(name="active_dev_badge", description="Use this if you are a developer of the bot")
async def active_dev_badge(interaction: discord.Interaction):
    await interaction.response.send_message("Claim your badge here (if you made this bot or are a developer of it) https://discord.com/developers/active-developer", ephemeral=True)

@tree.command(name="rules", description="DA RULES!!!!1111!!!!!1")
async def rules(interaction: discord.Interaction):
    embed = discord.Embed(title="Rules", description=requests.get("https://raw.githubusercontent.com/LizardRush/LizardRushBot/main/rules.txt").text)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="invite", description="Return the bot's invite link (owner only)")
async def invite(interaction: discord.Interaction):
    if interaction.user.id == 1056032871841792110:
        await interaction.response.send_message("This bot's invite link is https://discord.com/oauth2/authorize?client_id=1197661699826798622&permissions=8&integration_type=0&scope=bot", ephemeral=True)
    else:
        await interaction.response.send_message("You are NOT him", ephemeral=True)

@tree.command(name="trap", description="Mute a user")
@app_commands.describe(user="The person to trap")
async def trap(interaction: discord.Interaction, user: discord.User):
    if interaction.user.guild_permissions.manage_roles:
        if user.guild_permissions.administrator:
            await interaction.response.send_message("You cannot trap a user with administrative permissions.", ephemeral=True)
        else:
            try:
                trapped_role = discord.utils.get(interaction.guild.roles, name="trapped")
                if trapped_role is None:
                    trapped_role = await interaction.guild.create_role(name="trapped", permissions=discord.Permissions(send_messages=False, speak=False))
                await user.add_roles(trapped_role)
                await interaction.response.send_message(f"{user.display_name} has been trapped!", ephemeral=True)
                print_positive(f"Muted {user.display_name}")
            except Exception as e:
                print_negative(f"Error muting: {e}")
    else:
        await interaction.response.send_message("You need Manage Roles to mute members", ephemeral=True)
@tree.command(name="untrap", description="Unmute a user")
@app_commands.describe(user="The person to untrap")
async def untrap(interaction: discord.Interaction, user: discord.User):
    if interaction.user.guild_permissions.manage_roles:
        try:
            trapped_role = discord.utils.get(interaction.guild.roles, name="trapped")
            if trapped_role:
                await user.remove_roles(trapped_role)
                await interaction.response.send_message(f"{user.display_name} has been untrapped!", ephemeral=True)
                print_positive(f"Successfully unmuted {user.display_name}")
            else:
                await interaction.response.send_message("No trapped role found.", ephemeral=True)
                print_neutral(f"No trapped role found")
        except Exception as e:
            print_negative(f"Failed to umnmute: {e}")
    else:
        await interaction.response.send_message("You need Manage Roles to unmute members", ephemeral=True)

@tree.command(name="clear-user-messages", description="Clear a user's messages")
@app_commands.describe(user="The user to clear")
async def delete_guild_messages(interaction: discord.Interaction, user: discord.User):
    """Delete all messages from a specific user in a guild."""

    # Make sure the bot has permission to delete messages in all channels
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send("You do not have permission to manage messages.", ephemeral = True)
        print_negative("User does not have permissions")
        return
    await interaction.response.send_message(content="Attempting", ephemeral=True)
    # Iterate over each text channel in the guild
    for channel in interaction.guild.text_channels:
        try:
            # Fetch message history
            async for message in channel.history(limit=None):
                # Check if the message is from the specified user
                if message.author == user:
                    await message.delete()
                    print_positive(f"Deleted message from {user} in {channel.name}, '{message.content}'")
        except discord.Forbidden:
            # Handle the case where the bot doesn't have permission to read or delete messages in a channel
            print_neutral(f"Skipping {channel.name}, bot lacks permission.")
        except discord.HTTPException as e:
            # Handle any HTTP errors (rate limiting, etc.)
            print_neutral(f"Error deleting messages in {channel.name}: {e}")

    await interaction.response.edit_message(f"Deleted all messages from {user} in {interaction.guild.name}.", epheneral = True)

@tree.command(name="clear-guild", description="Clear a guild's messages")
async def delete_user_messages(interaction: discord.Interaction):
    """Delete all messages from a specific user in a guild."""

    # Make sure the bot has permission to delete messages in all channels
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send("You do not have permission to manage messages.", ephemeral = True)
        print_negative("User does not have permissions")
        return
    await interaction.response.send_message(content="Attempting", ephemeral=True)
    # Iterate over each text channel in the guild
    for channel in interaction.guild.text_channels:
        try:
            
            # Fetch message history
            async for message in channel.history(limit=None):
                await message.delete()
                print_positive(f"Deleted message in {channel.name}, '{message.content}'")
        except discord.Forbidden:
            # Handle the case where the bot doesn't have permission to read or delete messages in a channel
            print_neutral(f"Skipping {channel.name}, bot lacks permission.")
        except discord.HTTPException as e:
            # Handle any HTTP errors (rate limiting, etc.)
            print_neutral(f"Error deleting messages in {channel.name}: {e}")
        await interaction.response.edit_message(content="End")

    await interaction.response.send(f"Deleted all messages in {interaction.guild.name}.", epheneral = True)

@tree.command(name="clear-channel", description="Clear a channel's messages")
async def delete_user_messages(interaction: discord.Interaction):
    """Delete all messages from a specific user in a guild."""

    # Make sure the bot has permission to delete messages in all channels
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send("You do not have permission to manage messages.", ephemeral = True)
        print_negative("User does not have permissions")
        return

    # Iterate over each text channel in the guild
    await interaction.response.send_message(content="Attempting", ephemeral=True)
    try:
        # Fetch message history
        async for message in interaction.channel.history(limit=None):
            await message.delete()
            print_positive(f"Deleted message in {interaction.channel.name}, '{message.content}'")
        await interaction.response.edit_message(content="Success")
    except discord.Forbidden:
        # Handle the case where the bot doesn't have permission to read or delete messages in a channel
        print_neutral(f"Skipping {interaction.channel.name}, bot lacks permission.")
        await interaction.response.edit_message(content="Failed")
    except discord.HTTPException as e:
        # Handle any HTTP errors (rate limiting, etc.)
        await interaction.response.edit_message(content="Failed")
        print_neutral(f"Error deleting messages in {interaction.channel.name}: {e}")

os.system("clear")

post_file_to_github("LizardRush/LizardRushBot", "main.py", open("./main.py").read(), "Auto Update From Code")
try:
    asyncio.run(client.start(DISCORD_TOKEN))
except KeyboardInterrupt:
    print_neutral("Exitting...")
    exit()
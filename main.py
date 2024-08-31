import discord
import os
import aiohttp
import json
import asyncio
import requests
import re
import random
import yt_dlp
from datetime import timedelta, timezone, datetime
from github import Github, GithubException
from discord import app_commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv("./.env")

# Environment variables
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_KEY")
DISCORD_TOKEN = os.getenv("TOKEN")

# Constants
handle = "https://raw.githubusercontent.com/LizardRush/LizardRushBot/main/"
prefix = '!'
doors_prefix = "#"
hidden_command_channels = []
voice_client = None

# Initialize Discord Client
client = discord.Client(intents=discord.Intents.all())
tree = app_commands.CommandTree(client)
owner = client.get_user(json.load(open("config.json","r"))["owner"])

# Fetch JSON data
async def fetch_json(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            content = await response.text()
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                print(f"Failed to decode JSON. Content: {content}")
                return None

def get_video_status(video_url):
    video_id_match = re.search(r'(v=|be/|embed/|youtu\.be/|v/|shorts/|watch\?v=)([a-zA-Z0-9_-]{11})', video_url)
    
    if video_id_match:
        video_id = video_id_match.group(2)
    else:
        return None, None
    
    api_url = f"https://www.googleapis.com/youtube/v3/videos?id={video_id}&part=liveStreamingDetails,snippet&key={YOUTUBE_API_KEY}"
    response = requests.get(api_url)
    data = response.json()
    
    if 'items' not in data or not data['items']:
        return None, None

    video_data = data['items'][0]
    live_details = video_data.get('liveStreamingDetails')
    snippet = video_data.get('snippet')
    
    if live_details and 'scheduledStartTime' in live_details:
        scheduled_time = datetime.fromisoformat(live_details['scheduledStartTime'][:-1]).replace(tzinfo=timezone.utc)
        time_diff = scheduled_time - datetime.now(timezone.utc)
        
        if time_diff.total_seconds() > 0:
            # Format the timestamp in a friendly way
            hours, remainder = divmod(int(time_diff.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            parts = []
            if hours > 0:
                parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
            if minutes > 0:
                parts.append(f"{minutes} minute{'s' if minutes > 1 else ''}")
            if seconds > 0:
                parts.append(f"{seconds} second{'s' if seconds > 1 else ''}")
            timestamp = " and ".join(parts)
            return 'premiering', timestamp
    elif snippet and snippet.get('liveBroadcastContent') == 'none':
        return 'released', None

    return None, None


# Send DM to owner
async def dm_owner(message):
    owner = await client.fetch_user(1056032871841792110)
    await owner.send(message)

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
            print("File successfully updated in GitHub.")
        except GithubException as e:
            if e.status == 404:
                repo.create_file(file_path, commit_message, file_content)
                print("File successfully created in GitHub.")
            else:
                print(f"Failed to handle file: {e}")
    except GithubException as e:
        print(f"Failed to get repository: {e}")

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
async def generate_stats(user, ctx):
    if not user.bot:
        response = requests.get(f"{handle}/stats/{user.id}_stats.json")
        if response.status_code not in [200, 201]:
            try:
                post_file_to_github(
                    "LizardRush/LizardRushBot",
                    f"stats/{user.id}_stats.json",
                    json.dumps({
                        "Name": user.name,
                        "ID": user.id,
                        "Can_Restore": False,
                        "Coins": 0,
                        "Warnings": 0,
                        "Ticket_Banned": False,
                    }, indent=4),
                    f"Generated Stats For {user.display_name}",
                )
                if ctx:
                    await ctx.send(f'Created stats for {user.display_name}')
            except Exception as e:
                print(f"Error creating stats: {e}")
                if ctx:
                    await ctx.send(f'Failed to create stats for {user.display_name}')
    else:
        if ctx:
            await ctx.send(f'User is a bot: {user.display_name}')

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
                    "Can_Restore": False,
                    "Coins": 0,
                    "Warnings": 0,
                    "Ticket_Banned": False,
                }
# Client events
@client.event
async def on_ready():
    await setup_hook()
    print(f"Bot is ready and connected as {client.user}")

    if client.ws is not None:
        await client.change_presence(status=discord.Status.dnd)
    else:
        print("WebSocket connection is not established.")

    json_data = await fetch_json(f"{handle}config.json")
    if json_data:
        for channel_id in json_data.get("hidden_command_channels", []):
            hidden_command_channels.append(client.get_channel(channel_id))

@client.event
async def on_message(message):
    if message.author == client:
        return
    if isinstance(message.channel, discord.DMChannel):
        attachments = [attachment for attachment in message.attachments]
        embed = discord.Embed(title=message.author.name)
        embed.add_field(name="Message", value=message.content)
        if len(attachments) >= 1:
            embed.add_field(name="Attachments")
        await owner.create_dm()
        await owner.send(files=attachments, embed=embed)
        

@client.event
async def on_member_join(member):
    INVITE_LINK = "https://discord.gg/pJstGtrj6h"
    # Fetch the invite logs
    invites_before_join = await member.guild.invites()
    
    # Check the invite link used
    used_invite = None
    for invite in invites_before_join:
        if invite.code in INVITE_LINK:
            used_invite = invite
            break

    if used_invite:
        # Find the admin role in the server
        role = discord.utils.get(member.guild.roles, id=1198263479161856030)
        if role:
            await member.add_roles(role)
            await member.send(f'You have been granted the Admin rank in the server as you joined from te admin only server')

# Setup hook for command tree
async def setup_hook():
    try:
        await tree.sync()
    except Exception as e:
        print(f"Error syncing command tree: {e}")

# Command definitions
@tree.command(name="give_coins", description="Give a user some coins")
@app_commands.describe(user="The person to give them to", amount="Coins amount")
async def give_coins(interaction: discord.Interaction, user: discord.User, amount: int):
    if interaction.user.guild_permissions.administrator:
        data = await get_stats(user)
        data["Coins"] += amount
        post_file_to_github("LizardRush/LizardRushBot", f"stats/{user.id}_stats.json", json.dumps(data, indent=4))
        await interaction.response.send_message(f"Gave {amount} coins to {user.name}", ephemeral=True)
    else:
        if random.randint(1, 1000) == 1:
            await interaction.response.send_message("no, take this instead", ephemeral=True)
            await interaction.user.timeout(timedelta(days=random.randint(3, 60)))
        else:
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)

@tree.command(name="warn", description="Warn a user, if they get warned after they get 3 warnings they get banned")
@app_commands.describe(user="The person to warn")
async def warn(interaction: discord.Interaction, user: discord.User):
    data = await get_stats(user)
    if interaction.user.guild_permissions.administrator and not user.guild_permissions.administrator:
        if data['Warnings'] >= 3:
            await interaction.response.send_message(f'{user.display_name} has been banned for 3 warnings.', ephemeral=True)
            await user.ban(reason='3 warnings')
        else:
            data['Warnings'] += 1
            post_file_to_github("LizardRush/LizardRushBot", f"stats/{user.id}_stats.json", json.dumps(data, indent=4), f"Warned {user.display_name}")
            await interaction.response.send_message(f"Warned {user.display_name}", ephemeral=True)
    else:
        if random.randint(1, 1000) == 1:
            await interaction.response.send_message("no, take this instead", ephemeral=True)
            await interaction.user.timeout(timedelta(days=random.randint(3, 60)))
        else:
            await interaction.response.send_message("You cannot warn that user", ephemeral=True)

@tree.command(name="active_dev_badge", description="Use this if you are a developer of the bot")
async def active_dev_badge(interaction: discord.Interaction):
    await interaction.response.send_message("Claim your badge here (if you made this bot or are a developer of it) https://discord.com/developers/active-developer", ephemeral=True)

@tree.command(name="rules", description="DA RULES!!!!1111!!!!!1")
async def active_dev_badge(interaction: discord.Interaction):
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
            trapped_role = discord.utils.get(interaction.guild.roles, name="Trapped")
            if not trapped_role:
                trapped_role = await interaction.guild.create_role(name="Trapped", permissions=discord.Permissions.none())
            await user.add_roles(trapped_role)
            await interaction.response.send_message(f"{user.mention} has been trapped and cannot send messages.")
    else:
        if random.randint(1, 1000) == 1:
            await interaction.response.send_message("no, take this instead", ephemeral=True)
            await interaction.user.timeout(timedelta(days=random.randint(3, 60)))
        else:
            await interaction.response.send_message("You don't have the Manage Roles permission to use this command.", ephemeral=True)

@tree.command(name="crucifix", description="Ban a user")
@app_commands.describe(user="The person to crucify")
async def crucifix(interaction: discord.Interaction, user: discord.User):
    if interaction.user.guild_permissions.ban_members:
        await user.ban(reason=f'Crucified by {interaction.user.display_name}.')
        await interaction.response.send_message(f"{user.display_name} has been sacrificed for our sins.")
    else:
        await interaction.response.send_message("You don't have permission to ban members.", ephemeral=True)

@tree.command(name="unstuck", description="Untrap a user")
@app_commands.describe(user="The person to untrap")
async def unstuck(interaction: discord.Interaction, user: discord.User):
    if interaction.user.guild_permissions.manage_roles:
        trapped_role = discord.utils.get(interaction.guild.roles, name="Trapped")
        if trapped_role in user.roles:
            await user.remove_roles(trapped_role)
            await interaction.response.send_message(f"{user.display_name} has been untrapped.")
        else:
            await interaction.response.send_message(f"{user.display_name} is not trapped.", ephemeral=True)
    else:
        await interaction.response.send_message("You don't have the Manage Roles permission to use this command.", ephemeral=True)

@tree.command(name="clear", description="Clear a number of messages in a channel")
@app_commands.describe(amount="Number of messages to delete")
async def clear(interaction: discord.Interaction, amount: int):
    if interaction.user.guild_permissions.manage_messages:
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.response.send_message(f"Deleted {len(deleted)} messages.", ephemeral=True)
    else:
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)

# Start the bot
client.run(DISCORD_TOKEN)

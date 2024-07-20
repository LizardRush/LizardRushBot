import discord
import os
import aiohttp
import asyncio
import json
import requests
import subprocess
import dotenv
from datetime import datetime
from github import Github, GithubException
from discord import app_commands
from discord.ext import commands
from secrets import DISCORD_TOKEN, GITHUB_TOKEN
import logging

from dotenv import load_dotenv
load_dotenv()
# rest of the script

intents = discord.Intents.default()
intents.guilds = True
intents.guild_messages = True
intents.message_content = True

client = discord.Client(intents=intents)

def dict_to_permission_overwrite(permissions):
    return discord.PermissionOverwrite(
        allow=discord.Permissions(permissions["allow"]),
        deny=discord.Permissions(permissions["deny"])
)

allowed_members = []
class restore:
    servers = client.guilds

    async def run(self):
        try:
            for guild in self.servers:
                role_to_check = discord.utils.get(guild.roles, name="Bot")
                role_to_check2 = discord.utils.get(guild.roles, name="Authorized")
                backup_data = requests.get(f"https://raw.githubusercontent.com/LizardRush/LizardRushBot/main/backups/{guild.id}_backup.json")
                if backup_data.status_code == 200 or backup_data.status_code == 201:
                    backup_data = json.loads(backup_data.text)
                else:
                    continue
                async for i in guild.fetch_members():
                    if i.bot and role_to_check not in i.roles:
                        await i.ban(reason="Unauthorized Bot")
                    if role_to_check2 not in i.roles:
                        await i.ban(reason="Unauthorized Member")
                        await i.send("You have been banned from the server due to you not being Authorized")
                # Delete existing channels and categories
                for channel in guild.channels:
                    await channel.delete()
                await guild.edit(name=backup_data["Name"])
                # Restore categories and channels
                for category_name, category_info in backup_data.items():
                    new_category = await guild.create_category(category_info['name'])

                    # Restore category permissions
                    for perm in category_info['permissions']:
                        role = guild.get_role(perm['id'])
                        if role:
                            overwrite = dict_to_permission_overwrite(perm['permissions'])
                            await new_category.set_permissions(role, overwrite=overwrite)

                    for channel_name, channel_info in category_info['channels'].items():
                        if channel_info['type'] == 'text':
                            new_channel = await guild.create_text_channel(channel_info['name'], category=new_category)
                        elif channel_info['type'] == 'voice':
                            new_channel = await guild.create_voice_channel(channel_info['name'], category=new_category)
                        elif channel_info['type'] == 'news':
                            new_channel = await guild.create_text_channel(channel_info['name'], category=new_category)
                        elif channel_info['type'] == 'stage':
                            new_channel = await guild.create_stage_channel(channel_info['name'], category=new_category)
                        elif channel_info['type'] == 'forum':
                            new_channel = await guild.create_forum(channel_info['name'], category=new_category)

                        # Restore channel permissions
                        for perm in channel_info['permissions']:
                            role = guild.get_role(perm['id'])
                            if role:
                                overwrite = dict_to_permission_overwrite(perm['permissions'])
                                await new_channel.set_permissions(role, overwrite=overwrite)

                print(f'Restoration complete for {guild.name}')
                async for i in guild.fetch_members():
                    await i.send(f"Your server has been restored to the original state. If you have any questions or concerns, please contact the server owner.")
                    
        except Exception as e:
            print(f'An error occurred: {e}')

class backup:
    async def run():
        try:
            print(f'Logged in as {client.user}')
            for guild in client.guilds:
                role_to_check = discord.utils.get(guild.roles, name="Bot")
                role_to_check2 = discord.utils.get(guild.roles, name="Authorized")
                backup_data = requests.get(f"https://raw.githubusercontent.com/LizardRush/LizardRushBot/main/backups/{guild.id}_backup.json")
                if backup_data.status_code == 200 or backup_data.status_code == 201:
                    backup_data = json.loads(backup_data.text)
                else:
                    continue
                async for i in guild.fetch_members():
                    if i.bot and role_to_check not in i.roles:
                        await i.ban(reason="Unauthorized Bot")
                    if role_to_check2 not in i.roles:
                        await i.ban(reason="Unauthorized Member")
                        await i.send("You have been banned from the server due to you not being Authorized")
                # Delete existing channels and categories
                for channel in guild.channels:
                    await channel.delete()
                await guild.edit(name=backup_data["Name"])
                # Restore categories and channels
                for category_name, category_info in backup_data.items():
                    new_category = await guild.create_category(category_info['name'])

                    # Restore category permissions
                    for perm in category_info['permissions']:
                        role = guild.get_role(perm['id'])
                        if role:
                            overwrite = dict_to_permission_overwrite(perm['permissions'])
                            await new_category.set_permissions(role, overwrite=overwrite)

                    for channel_name, channel_info in category_info['channels'].items():
                        if channel_info['type'] == 'text':
                            new_channel = await guild.create_text_channel(channel_info['name'], category=new_category)
                        elif channel_info['type'] == 'voice':
                            new_channel = await guild.create_voice_channel(channel_info['name'], category=new_category)
                        elif channel_info['type'] == 'news':
                            new_channel = await guild.create_text_channel(channel_info['name'], category=new_category)
                        elif channel_info['type'] == 'stage':
                            new_channel = await guild.create_stage_channel(channel_info['name'], category=new_category)
                        elif channel_info['type'] == 'forum':
                            new_channel = await guild.create_forum(channel_info['name'], category=new_category)

                        # Restore channel permissions
                        for perm in channel_info['permissions']:
                            role = guild.get_role(perm['id'])
                            if role:
                                overwrite = dict_to_permission_overwrite(perm['permissions'])
                                await new_channel.set_permissions(role, overwrite=overwrite)

                print(f'Restoration complete for {guild.name}')
                async for i in guild.fetch_members():
                    await i.send(f"Your server has been restored to the original state. If you have any questions or concerns, please contact the server owner.")
                    
        except Exception as e:
            print(f'An error occurred: {e}')
# GitHub Authentication


def post_file_to_github(repo_name, file_path, file_content, commit_message, token=GITHUB_TOKEN):

    # Authenticate with GitHub
    g = Github(token)

    try:
        # Get the repository
        repo = g.get_repo(repo_name)

        # Check if the file exists
        try:
            contents = repo.get_contents(file_path)
            # If file exists, update it
            repo.update_file(file_path, commit_message, file_content, contents.sha)
            print("File successfully updated in GitHub.")
        except GithubException as e:
            if e.status == 404:
                # If file does not exist, create it
                repo.create_file(file_path, commit_message, file_content)
                print("File successfully created in GitHub.")
            else:
                print(f"Failed to handle file: {e}")

    except GithubException as e:
        print(f"Failed to get repository: {e}")


intents = discord.Intents.all()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)

handle = "https://raw.githubusercontent.com/LizardRush/LizardRushBot/main/"
prefix = '!'
doors_prefix = "#"
hidden_command_channels = []
voice_client = None

async def fetch_json(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            content = await response.text()
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                print(f"Failed to decode JSON. Content: {content}")
                return None




async def create_embed(description="", title="", picture="", color=0x000000, subtitle="", footer="", timestamp=None):
    embed = discord.Embed(description=description, title=title, color=color)
    if picture:
        embed.set_image(url=picture)
    if subtitle:
        embed.add_field(name="Subtitle", value=subtitle, inline=False)
    if footer:
        embed.set_footer(text=footer)
    embed.timestamp = timestamp
    return embed

async def say_as(channel, identity, avatar_url, message):
    webhook = await channel.create_webhook(name=identity)
    await webhook.send(content=message, username=identity, avatar_url=avatar_url)
    await webhook.delete()

async def make_http_request(ctx, method, url):
    async with aiohttp.ClientSession() as session:
        async with getattr(session, method.lower())(url) as response:
            status_message = f"HTTP {method} request status for {url}: {response.status}"
            if method.upper() == 'GET':
                content = await response.text()
                status_message += f"\nResponse Content:\n```{content}```"
            await ctx.send(status_message)

class console:
    @staticmethod
    async def clear():
        os.system('cls' if os.name == 'nt' else 'clear')

async def setup():
    guild_id = 1197655423621267516  # Replace with your guild ID
    guild = discord.Object(id=guild_id)

    # Register slash commands
    commands_list = [
        {
            "name": "give_coins",
            "description": "Give coins to a user",
            "options": [
                {
                    "type": discord.AppCommandOptionType.USER,
                    "name": "user",
                    "description": "The person to give coins to",
                    "required": True
                },
                {
                    "type": discord.AppCommandOptionType.INTEGER,
                    "name": "amount",
                    "description": "Amount of coins to give",
                    "required": True
                }
            ]
        },
        {
            "name": "warn",
            "description": "Warn a user",
            "options": [
                {
                    "type": discord.AppCommandOptionType.USER,
                    "name": "user",
                    "description": "The person to warn",
                    "required": True
                }
            ]
        },
        {
            "name": "invite",
            "description": "Get this bot's invite link"
        },
        {
            "name": "trap",
            "description": "Trap a user",
            "options": [
                {
                    "type": discord.AppCommandOptionType.USER,
                    "name": "user",
                    "description": "The person to trap",
                    "required": True
                }
            ]
        },
        {
            "name": "crucifix",
            "description": "Crucify a user",
            "options": [
                {
                    "type": discord.AppCommandOptionType.USER,
                    "name": "user",
                    "description": "The person to crucify",
                    "required": True
                }
            ]
        },
        {
            "name": "crucifix_trapped",
            "description": "Crucify all trapped users"
        },
        {
            "name": "grant_admin",
            "description": "Grant admin permissions to a user",
            "options": [
                {
                    "type": discord.AppCommandOptionType.USER,
                    "name": "user",
                    "description": "The person to grant admin permissions to",
                    "required": True
                }
            ]
        },
        {
            "name": "send_rules",
            "description": "Send the server rules"
        }
    ]

    for command in commands_list:
        await client.application_command.create(
            name=command["name"],
            description=command["description"],
            guild=guild,
            options=command.get("options", [])
        )

@client.event
async def on_ready():
    logging.debug(f"Bot is ready and connected as {client.user}")
    global terminal_channel
    await setup()
    if client.ws is not None:
        await client.change_presence(status=discord.Status.dnd)
    else:
        print("WebSocket connection is not established.")
    
    json_data = await fetch_json(f"{handle}config.json")
    if json_data:
        for channel_id in json_data.get("hidden_command_channels", []):
            hidden_command_channels.append(client.get_channel(channel_id))
    
    terminal_channel = discord.utils.get(client.get_all_channels(), name="terminal")
    if terminal_channel:
        print(f"Terminal channel found: {terminal_channel.name}")
    else:
        print("Terminal channel not found.")
    try:
        synced = await client.tree.sync()
        print(f"synced {len(synced)} commands")
    except Exception as e:
        print(e)

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


@client.event
async def on_application_command(interaction: discord.Interaction):
    command_name = interaction.data["name"]
    
    if command_name == "give_coins":
        await give_coins(interaction)
    elif command_name == "warn":
        await warn(interaction)
    elif command_name == "invite":
        await invite(interaction)
    elif command_name == "trap":
        await trap(interaction)
    elif command_name == "crucifix":
        await crucifix(interaction)
    elif command_name == "crucifix_trapped":
        await crucifix_trap(interaction)
    elif command_name == "grant_admin":
        await grant_admin(interaction)
    elif command_name == "send_rules":
        await send_rules(interaction)

async def give_coins(interaction: discord.Interaction):
    user_id = interaction.data["options"][0]["value"]
    amount = interaction.data["options"][1]["value"]
    
    user = interaction.guild.get_member(user_id)
    
    if interaction.user.guild_permissions.administrator:
        # Your logic to give coins
        await interaction.response.send_message(f"Gave {amount} coins to {user.name}", ephemeral=True)
    else:
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)

async def warn(interaction: discord.Interaction):
    user_id = interaction.data["options"][0]["value"]
    user = interaction.guild.get_member(user_id)
    
    if interaction.user.guild_permissions.administrator and not user.guild_permissions.administrator:
        # Your logic to warn the user
        await interaction.response.send_message(f"Warned {user.display_name}", ephemeral=True)
    else:
        await interaction.response.send_message("You cannot warn that user.", ephemeral=True)

async def invite(interaction: discord.Interaction):
    await interaction.response.send_message("This bot's invite link is [https://discord.gg/LizardBot](https://discord.com/oauth2/authorize?client_id=1197661699826798622&permissions=8&integration_type=0&scope=bot)", ephemeral=True)

async def trap(interaction: discord.Interaction):
    user_id = interaction.data["options"][0]["value"]
    user = interaction.guild.get_member(user_id)
    
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
        await interaction.response.send_message("You don't have the Manage Roles permission to use this command.", ephemeral=True)

async def crucifix(interaction: discord.Interaction):
    user_id = interaction.data["options"][0]["value"]
    user = interaction.guild.get_member(user_id)
    
    if interaction.user.guild_permissions.ban_members:
        if user.guild_permissions.administrator:
            await interaction.response.send_message("You cannot crucify a user with administrative permissions.", ephemeral=True)
        else:
            trapped_role = discord.utils.get(interaction.guild.roles, name="Trapped")
            if not trapped_role:
                trapped_role = await interaction.guild.create_role(name="Trapped", permissions=discord.Permissions.none())
            await user.add_roles(trapped_role)
            await interaction.response.send_message(f"{user.mention} has been trapped and cannot send messages.")
    else:
        await interaction.response.send_message("You don't have the Ban Users permission to use this command.", ephemeral=True)

async def crucifix_trap(interaction: discord.Interaction):
    if interaction.user.guild_permissions.ban_members:
        trapped_role = discord.utils.get(interaction.guild.roles, name="Trapped")
        if trapped_role:
            trapped_members = [member for member in interaction.guild.members if trapped_role in member.roles]
            for member in trapped_members:
                try:
                    await interaction.guild.ban(member)
                    await interaction.response.send_message(f"{member.mention} has been banned.")
                except discord.Forbidden:
                    await interaction.response.send_message("I don't have the necessary permissions to ban members.")
        else:
            await interaction.response.send_message("No one is trapped.", ephemeral=True)
    else:
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)

async def grant_admin(interaction: discord.Interaction):
    user_id = interaction.data["options"][0]["value"]
    user = interaction.guild.get_member(user_id)
    
    if interaction.user.guild_permissions.administrator:
        admin_role = discord.utils.get(interaction.guild.roles, name="Admin")
        if not admin_role:
            admin_role = await interaction.guild.create_role(name="Admin", permissions=discord.Permissions(administrator=True))
        await user.add_roles(admin_role)
        await interaction.response.send_message(f"{user.mention} has been granted admin permissions.")
    else:
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)

async def send_rules(interaction: discord.Interaction):
    if interaction.user.guild_permissions.administrator:
        # Assuming you have a URL or path to your rules file
        rules_url = "https://raw.githubusercontent.com/LizardRush/LizardRushBot/main/rules.txt"
        rules_text = requests.get(rules_url).text
        embed = discord.Embed(color=0x0D98BA, description=rules_text.replace("\n", "\n\n"), title="Da Rules")
        channel = discord.utils.get(interaction.guild.channels, name="rulebook")
        if channel:
            await channel.send(embed=embed)
            await interaction.response.send_message("Rules sent to the rulebook channel.", ephemeral=True)
        else:
            await interaction.response.send_message("Rulebook channel not found.", ephemeral=True)
    else:
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)

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
                }

def get_public_ip():
    response = requests.get('https://api.ipify.org?format=json')
    ip = response.json()['ip']
    return ip

async def execute_command(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
        output = result.stdout if result.returncode == 0 else result.stderr
        return output
    except subprocess.CalledProcessError as e:
        return f"Command failed with error: {e}"
    except Exception as e:
        return f"An error occurred: {e}"

@client.event
async def on_message(message):
    print(f"Received message: {message.content} from channel: {message.channel.name}")
    if message.author.bot:
        return

    if message.channel == terminal_channel:
        command = message.content

        if command.startswith(f'LizardBot {DISCORD_TOKEN} forceban'):
            user_id = command.split(' ')[3]
            user = await message.guild.get_user(int(user_id))
            await user.ban(reason="Force Banned through terminal")
            await message.channel.send(f"```Banned {user.display_name}```")

        elif command.startswith(f'LizardBot {DISCORD_TOKEN} backup'):
            await message.delete()
            await backup.run()
            await message.channel.send("```Backed up all guilds```")

        elif command.startswith(f'LizardBot {DISCORD_TOKEN} restore'):
            await message.delete()
            parts = command.split(' ')
            server_id = int(parts[3]) if len(parts) > 3 else None
            restore.guilds = await client.get_guild(server_id) if server_id else client.guilds
            await restore.run()
            terminal_channel = discord.utils.get(message.guild.channels, "terminal")
            await terminal_channel.send("```Restored guild(s), it is safe to return to your activities```")
        elif command.startswith("clear"):
            await terminal_channel.purge(limit=None)
            return
            
        else:
            try:
                output = await execute_command(command)
                await message.channel.send(f"```\n{output}\n```")
                print(output)
            except Exception as e:
                await message.channel.send(f"Error executing command: {e}")
                print(f"Error executing command: {e}")

    if message.guild is not None:
        # Access "hidden_command_channels" correctly
        json_file = requests.get(f"{handle}config.json")
        if json_file.status_code == 200:
            for i in json.loads(json_file.text)["hidden_command_channels"]:
                hidden_command_channels.append(client.get_channel(i))
    try:
        if message.channel == discord.utils.get(message.guild.channels, name="ohio-announcements"):
            await message.publish()
    except:
        print("\n")
    if message.author.bot:
        return
    if isinstance(message.channel, discord.DMChannel):
        embed_message = create_embed(
            title=f"{message.author.display_name} Sent A Message",
            description=message.content,
            picture=message.author.avatar.url,
            footer=f"Sent by {message.author.name}",
            timestamp=datetime.now()
        )
        owner = await client.fetch_user(1056032871841792110)
        await owner.send(embed=embed_message)
        return
    if message.content.startswith(f"{prefix}give_coins"):
        if message.author.guild_permissions.administrator:
            try:
                user = message.mentions[0]
                amount = int(message.content.split()[2])
                data = get_stats(user)
                data["Coins"] += amount
                post_file_to_github("LizardRushBot", f"stats/{user.id}_stats.json", json.dumps(data, indent=4))
                await message.channel.send(f"Gave {amount} coins to {user.name}")
            except (IndexError, ValueError):
                await message.channel.send("Invalid command format. Use: !give_coins @user amount")
        else:
            await message.channel.send("You don't have permission to use this command.")
    if message.content.startswith(f"{prefix}invite"):
        await message.reply("This bot's invite link is [https://discord.gg/LizardBot](https://discord.com/oauth2/authorize?client_id=1197661699826798622&permissions=8&integration_type=0&scope=bot)")

    if message.content.startswith(f"{prefix}warn"):
        for i in message.mentions:
            if not os.path.exists(f"ohio/variables/stats/{i.id}_stats.json"):
                await generate_stats(i, None)
            with open(f'ohio/variables/stats/{i.id}_stats.json', 'r+') as f:
                data = json.load(f)
                if message.author.guild_permissions.administrator:
                    if data['Warnings'] == 3:
                        await message.reply(f'{i.name} has been banned for 3 warnings.')
                        await i.ban(reason='3 warnings')
                    else:
                        data['Warnings'] += 1
                        f.seek(0)
                        json.dump(data, f, indent=4)
                        await message.reply(f'Warned {i.mention}')
                else:
                    await message.reply(f'You do not have permission to warn {i.mention}')

    print(f'{message.author.name} sent: {message.content}')

    if message.content.startswith(f'{prefix}trap'):
        user_mentions = message.mentions
        if user_mentions:
            if message.author.guild_permissions.manage_roles:
                for user in user_mentions:
                    # Check if the mentioned user has administrative permissions
                    if user.guild_permissions.administrator:
                        await message.reply("You cannot trap a user with administrative permissions.")
                    else:
                        trapped_role = discord.utils.get(message.guild.roles, name="Trapped")
                        if not trapped_role:
                            trapped_role = await message.guild.create_role(name="Trapped", permissions=discord.Permissions.none())
                        await user.add_roles(trapped_role)
                    await message.reply(f"{user.mention} has been trapped and cannot send messages.")
            else:
                await message.reply("You don't have the Manage Roles permission to use this command.")
        else:
            await message.reply("Please mention a user.")

    if message.content.startswith(f'{doors_prefix}crucifix_trapped'):
        if message.author.guild_permissions.administrator:
            trapped_role = discord.utils.get(message.guild.roles, name="Trapped")
            if trapped_role:
                trapped_members = [member for member in message.guild.members if trapped_role in member.roles]
                for member in trapped_members:
                    try:
                        await message.guild.ban(member)
                        await message.reply(f"{member.mention} has been banned.")
                    except discord.Forbidden:
                        await message.reply("I don't have the necessary permissions to ban members.")
            else:
                await message.reply("No one is trapped.")
        else:
            await message.reply("You don't have permission to use this command.")

    elif message.content.startswith(f'{doors_prefix}crucifix'):
        user_mentions = message.mentions
        if user_mentions:
            if message.author.guild_permissions.ban_members:
                for user in user_mentions:
                    try:
                        await message.guild.ban(user)
                        await message.reply(f"{user.mention} has been crucified.")
                    except discord.Forbidden:
                        await message.reply("I don't have the necessary permissions to ban members.")
                    except Exception as e:
                        await message.reply(f"An error occurred: {str(e)}")
                        raise e
            else:
                await message.reply("You don't have the Ban Members permission to use this command.")
        else:
            await message.reply("Please mention a user to crucify.")

    if message.content.startswith(f'{prefix}grant_admin'):
        user_mentions = message.mentions
        if user_mentions:
            user = user_mentions[0]
            if message.author.guild_permissions.administrator:
                admin_role = discord.utils.get(message.guild.roles, name="Admin")
                if not admin_role:
                    admin_role = await message.guild.create_role(name="Admin", permissions=discord.Permissions(administrator=True))
                await user.add_roles(admin_role)
                await message.reply(f"{user.mention} has been granted admin permissions.")
            else:
                await message.reply("You don't have permission to use this command.")
        else:
            await message.reply("Please mention a user.")

    if message.content.startswith(f'{prefix}generate_stats'):
        if message.author.guild_permissions.administrator:
            async for i in message.guild.fetch_members(limit=None):
                await generate_stats(i, message.channel)

    if message.content.startswith(prefix) or message.content.startswith(doors_prefix):
        if message.channel in hidden_command_channels:
            await message.delete()

client.run(DISCORD_TOKEN)

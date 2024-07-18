from dotenv import load_dotenv
load_dotenv()
# rest of the script

import discord
import json
import os
import requests

intents = discord.Intents.default()
intents.guilds = True
intents.guild_messages = True
intents.message_content = True

client = discord.Client(intents=intents)

allowed_members = []

servers = client.guilds

def dict_to_permission_overwrite(permissions):
    return discord.PermissionOverwrite(
        allow=discord.Permissions(permissions["allow"]),
        deny=discord.Permissions(permissions["deny"])
    )

@client.event
async def on_ready():
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

    await client.close()

def run():
    client.run({{repl.git_token}})

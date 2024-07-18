import discord, shutil, os, time, aiohttp, random, asyncio, json, restore, requests, support
from variables import append, jsonify
from pydub import AudioSegment
from pydub.playback import play
from datetime import datetime
intents = discord.Intents.all()
intents.message_content = True
intents.members = True
prefix, doors_prefix, client, = append(
    '!',
    '#',
    discord.Client(command_prefix='!', intents=intents),
)
json_file = open('ohio/variables/globalConfig.json', 'r+')
hidden_command_channels = []
voice_client = None

update_path = "ohio/variables/message/update.md"

class DiscordVoiceReceiver(discord.AudioSource):
    """Custom AudioSource to receive audio data"""
    def __init__(self):
        super().__init__()

    def read(self):
        global audio_buffer
        if audio_buffer:
            data = audio_buffer.pop(0)
            return data
        else:
            return b''


async def join(ctx, user):
    """Joins the voice channel of the command issuer"""
    if user.voice:
        channel = user.voice.channel
        await channel.connect()
        await ctx.send(f"Joined {channel}")
        
    else:
        await ctx.send("You are not connected to a voice channel.")

async def leave(ctx):
    """Leaves the voice channel"""
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Disconnected from the voice channel.")
    else:
        await ctx.send("I'm not in a voice channel.")

def create_embed(description="", title="", picture="", color=0x000000, subtitle="", footer="", timestamp=None):
    # Create the embed object
    embed = discord.Embed(
        description=description,
        title=title,
        color=color
    )

    # Add picture if provided
    if picture:
        embed.set_image(url=picture)

    # Add subtitle if provided
    if subtitle:
        embed.add_field(name="Subtitle", value=subtitle, inline=False)

    # Add footer if provided
    if footer:
        embed.set_footer(text=footer)

    embed.timestamp = timestamp

    return embed

async def say_as(channel=None, identity="", avatar_url="https://cdn.discordapp.com/avatars/1197661699826798622/c5069aaa62d6b07084777791eed1afad.png?size=4096", *, message: str):
    # Create a webhook
    webhook = await channel.create_webhook(name=identity)

    # Use the webhook to send the message
    await webhook.send(
        content=message,
        username=identity,
        avatar_url=avatar_url
    )

    # Delete the webhook
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
            
@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.dnd)
    for i in json.load(json_file)["hidden_command_channels"]:
        hidden_command_channels.append(client.get_channel(i))
    await console.clear()
    print('Bot Logged In!')
    dirlist = os.listdir('__pycache__')
    channel = client.get_channel(1199826475969425478)
    for file in dirlist:
        shutil.move(f'__pycache__/{file}', f'ohio/cache/{file}')
    os.rmdir('__pycache__')
async def generate_stats(user, ctx):
    if not os.path.exists(f'ohio/variables/stats/{user.id}_stats.json') and not user.bot:
        with open(f'ohio/variables/stats/{user.id}_stats.json', 'w') as f:
            json.dump(
                
                {
                    "Name": user.name,
                    "ID": user.id,
                    "Can_Restore": False,
                    "Coins": 0,
                    "Warnings": 0,
                },
                f,
                indent=4
            )
            if ctx:
                await ctx.send(f'Created stats for {user.display_name}')
    else:
        await ctx.send(f'User is a bot: {user.display_name}')
def get_public_ip():
    response = requests.get('https://api.ipify.org?format=json')
    ip = response.json()['ip']
    return ip
@client.event
async def on_message(message):
    if message.guild is not None:
        # Access "hidden_command_channels" correctly
        json_file = open('ohio/variables/globalConfig.json')
        for i in json.load(json_file)["hidden_command_channels"]:
            hidden_command_channels.append(client.get_channel(i))
    try:
        if message.channel == discord.utils.get(message.guild.channels, name="ohio-announcements"):
            await message.publish()
    except:
        print("\n")
    if message.author.bot:
        return
    if isinstance(message.channel, discord.DMChannel):
        message = create_embed(title=f"{message.author.display_name} Sent A Message", description=message.content, picture=message.author.avatar.url,footer=f"Sent by {message.author.name}", timestamp=datetime.now())
        owner = await client.fetch_user(1056032871841792110)
        await owner.send(embed=message)
        return
    if message.content.startswith('!ip'):
        ip = get_public_ip()
        geolocation = requests.get("https://geo.ipify.org/api/v2/country,city?apiKey=at_UfD22rvN5SrZNgHrez2BXyhx4kbcZ&ipAddress={}".format(ip))
        if geolocation.status_code == 200:
            geo_data = geolocation.json()
            await message.reply(f'My public IP address is: {ip}, my geolocation is: Country: {geo_data["location"]["country"]}, City: {geo_data["location"]["city"]}')
        else:
            await message.reply(f'My public IP address is: {ip}, but I could not retrieve geolocation information.')
    if message.content.startswith(f"{prefix}give_coins"):
        if message.author.guild_permissions.administrator:
            try:
                user = message.mentions[0]
                amount = int(message.content.split()[2])
                if not os.path.exists(f'ohio/variables/stats/{user.id}_stats.json'):
                    await generate_stats(user, message)
                with open(f'ohio/variables/stats/{user.id}_stats.json', 'r+') as f:

                    data = json.load(f)
                    data["Coins"] += amount
                    f.seek(0)
                    json.dump(data, f, indent=4)
                    f.truncate()
                    await message.channel.send(f"Gave {amount} coins to {user.name}")
            except (IndexError, ValueError):
                await message.channel.send("Invalid command format. Use: !give_coins @user amount")
        else:
            await message.channel.send("You don't have permission to use this command.")
    if message.content.startswith(f"{prefix}invite"):
        await message.reply("This bot's invite link is [https://discord.gg/LizardBot](https://discord.com/oauth2/authorize?client_id=1197661699826798622&permissions=8&integration_type=0&scope=bot)")



    if message.content.startswith(f"{prefix}restore"):
        if json.load(open(f'ohio/variables/stats/{message.author.id}_stats.json', 'r'))["Can_Restore"]:
            await message.delete()
            restore.servers = message.guild
            restore.run()
            await client.close()

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

    if message.content.startswith(f'{prefix}announce_update'):
        if message.author.guild_permissions.administrator:
            announcements_channel = discord.utils.get(message.guild.channels, name="ohio-announcements")
            await say_as(identity="Ohio Airlines Update", avatar_url=discord.utils.get(message.guild.channels, name="ohio-announcements").guild.icon.url, channel=announcements_channel, message=f"New Ohio Airlines Update\n\n{open(update_path, 'r').read()}")

    if message.content.startswith(f'{prefix}http_get'):
        url = message.content[len(f'{prefix}http_get '):].strip()
        await make_http_request(message.channel, 'GET', url)

    elif message.content.startswith(f'{prefix}http_post'):
        url = message.content[len(f'{prefix}http_post '):].strip()
        await make_http_request(message.channel, 'POST', url)

    elif message.content.startswith(f'{prefix}http_put'):
        url = message.content[len(f'{prefix}http_put '):].strip()
        await make_http_request(message.channel, 'PUT', url)

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

    if message.content.startswith(f'{prefix}update_rulebook') and message.author.guild_permissions.admin:
        target_channel_id = "rulebook"
        channel = discord.utils.get(message.guild.channels, name=target_channel_id)
        if channel:
            try:
                if os.path.exists('ohio/variables/message/id.txt'):
                    with open('ohio/variables/message/id.txt', 'r') as f:
                        msg = await channel.fetch_message(int(f.read()))
                        await msg.delete()
                with open('ohio/variables/message/Rulebook.md', 'r') as f:
                    msg = await channel.send(f.read())
                    with open('ohio/variables/message/id.txt', 'w') as f:
                        f.write(f'{msg.id}')
                await message.author.send("Rulebook has been updated and shared on Discord.")
            except Exception as e:
                print(f"Error: {e}")
                await message.author.send("Error updating the rulebook.")
        else:
            await message.author.send("Error: Channel not found.")

    if message.content.startswith(f'{prefix}commands'):
        with open('ohio/variables/message/commands.md', 'r') as f:
            await message.reply(f.read())

    if message.content.startswith(f'{prefix}dm_owner'):
        owner = await client.fetch_user(1056032871841792110)
        if owner:
            content = message.content[len(f'{prefix}dm_owner '):].strip()
            await owner.send(f"Message from {message.author.display_name} ({message.author.mention}): {content}")
            await message.delete()
            msg = await message.author.send("Your message has been sent to the bot owner.")
            time.sleep(5)
            await msg.delete()
        else:
            msg = await message.author.send("Could not find the bot owner.")
            await message.delete()
            time.sleep(5)
            await msg.delete()

    if message.content.startswith(f'{prefix}generate_stats'):
        if message.author.guild_permissions.administrator:
            async for i in message.guild.fetch_members(limit=None):
                await generate_stats(i, message.channel)

    if message.content.startswith(prefix) or message.content.startswith(doors_prefix):
        if message.channel in hidden_command_channels:
            await message.delete()

    
@client.event
async def on_guild_join(guild):
    main_channel = guild.system_channel
    user = await client.fetch_user(1056032871841792110)
    await user.create_dm()
    invite = await main_channel.create_invite()
    await user.dm_channel.send(f"Joined Guild: {invite.url}")
    if main_channel:
        await main_channel.send(f"Hello! I am your new bot. Here is some information about me.\nI am currently in {len(client.guilds)} servers.\nYou can use me by sending commands starting with '!'\nUse !commands to list all commands")
@client.event
async def on_member_join(user):
    await generate_stats(user, None)
    await user.channel.send('{} welcome to ohio airlines, how would you like your flight to be?'.format(user.mention))
try:
    token = os.getenv("TOKEN") or ""
    if token == "":
        raise Exception("Please add your token to the Secrets pane.")
    client.run(token)
except KeyboardInterrupt:
    asyncio.run(client.close())
except Exception as e:
    raise e

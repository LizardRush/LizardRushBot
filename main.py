import discord, shutil, os, time, aiohttp, random, asyncio, json, requests
from pydub import AudioSegment
from pydub.playback import play
from datetime import datetime
import base64
from github import Github

def post_file_to_github(repo_name, file_path, file_content, commit_message, token=os.environ["GIT_TOKEN"]):
    # Authenticate with GitHub
    g = Github(token)

    # Get the repository
    try:
        repo = g.get_repo(repo_name)
    except Exception as e:
        print(f"Failed to get repository: {e}")
        return

    # Check if the file exists
    try:
        contents = repo.get_contents(file_path)
        # If file exists, update it
        repo.update_file(file_path, commit_message, file_content, contents.sha)
        print("File successfully updated in GitHub.")
    except Exception as e:
        # If file does not exist, create it
        repo.create_file(file_path, commit_message, file_content)
        print("File successfully created in GitHub.")

intents = discord.Intents.all()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)

handle = "https://raw.githubusercontent.com/LizardRush/LizardRushBot/main/"

prefix = '!'
doors_prefix = '#'
json_file = requests.get(f"{handle}config.json")
if json_file.status_code == 200:
    json_file = json.loads(json_file.text)
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
    json_file = requests.get(f"{handle}config.json")
    if json_file.status_code == 200:
        for i in json.loads(json_file.text)["hidden_command_channels"]:
            hidden_command_channels.append(client.get_channel(i))
    await console.clear()
    print('Bot Logged In!')
    dirlist = os.listdir('__pycache__')
    channel = client.get_channel(1199826475969425478)
    for file in dirlist:
        shutil.move(f'__pycache__/{file}', f'ohio/cache/{file}')
    os.rmdir('__pycache__')

async def generate_stats(user, ctx):
    if not user.bot and requests.get(f"{handle}/stats/{user.id}_stats.json") not in [200, 201]:
        post_file_to_github(
            "LizardRushBot",
            f"stats/{user.id}_stats.json",
            json.dumps({
                "Name": user.name,
                "ID": user.id,
                "Can_Restore": False,
                "Coins": 0,
                "Warnings": 0,
            },
            indent=4),
            f"Generated Stats For {user.display_name}",
        )
        if ctx:
            await ctx.send(f'Created stats for {user.display_name}')
    else:
        await ctx.send(f'User is a bot: {user.display_name}')

async def get_stats(user):
    stats = requests.get(f"{handle}/stats/{user.id}_stats.json")
    if stats.status_code in [200, 201]:
        return json.loads(stats.text)
    elif stats.status_code == 404:
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

@client.event
async def on_message(message):
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

                data = await get_stats(user)
                data["Coins"] += amount
                post_file_to_github("LizardRushBot", f"stats/{user.id}_stats.json", json.dumps(data), f"Gave Coins To {user.display_name}")
                await message.channel.send(f"Gave {amount} coins to {user.name}")
            except (IndexError, ValueError):
                await message.channel.send("Invalid command format. Use: !give_coins @user amount")
        else:
            await message.channel.send("You don't have permission to use this command.")

    if message.content.startswith(f"{prefix}invite"):
        await message.reply("This bot's invite link is [https://discord.gg/L4gBB4R6Ws](https://discord.gg/L4gBB4R6Ws)")

    if message.content.startswith(f"{prefix}voice"):
        if message.author.guild_permissions.administrator:
            if message.content == f"{prefix}voice join":
                await join(message.channel, message.author)
            elif message.content == f"{prefix}voice leave":
                await leave(message.channel)
        else:
            await message.channel.send("You don't have permission to use this command.")

    if message.content.startswith(f"{prefix}update_rulebook"):
        if message.author.guild_permissions.administrator:
            command = message.content.replace(f"{prefix}update_rulebook ", "")
            command = command.split(" ")
            if command[0] == "list":
                message_str = ""
                for command in json_file["rulebook_commands"]:
                    message_str += f"{command}\n"
                await message.reply(message_str)
            elif command[0] == "add":
                json_file["rulebook_commands"][command[1]] = command[2]
                post_file_to_github("LizardRushBot", "config.json", json.dumps(json_file), f"Added rulebook command {command[1]} to config.json")
                await message.reply(f"Added rulebook command {command[1]}")
            elif command[0] == "remove":
                del json_file["rulebook_commands"][command[1]]
                post_file_to_github("LizardRushBot", "config.json", json.dumps(json_file), f"Removed rulebook command {command[1]} from config.json")
                await message.reply(f"Removed rulebook command {command[1]}")
        else:
            await message.reply("You do not have the permission to use this command.")
            
client.run(os.environ["TOKEN"])

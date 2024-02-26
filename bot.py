import json, discord, asyncio, os, time, datetime, sqlite3, random, scrapetube, requests, easy_pil
from discord.ext import commands, tasks
from easy_pil import Editor, load_image_async, Font
from Commands.members import mAddBtn

with open("Data/config.json", "r+", encoding="utf-8") as f: config = json.load(f)
previous, notified = [], []

with open("Data/config.json", "r+", encoding="utf-8") as f: 
    config = json.load(f)
    token = config["token"]
    twitchid = config["twitch"]
    clientid = config["clientid"]
    clientsecret = config["clientsecret"]
    ytchannel = config["ytchannel"]
    youtubeid = config["youtube"]
    welcomeid = config["welcome"]
    modmailid = config["modmail"]


try:
    for results in [scrapetube.get_channel(config["ytchannel"], sort_by="newest", limit=3, content_type=ctype) for ctype in ["videos", "shorts", "streams"]]:
        [previous.append(result['videoId']) for result in results if result['videoId'] not in previous]
    print("Scraping YouTube channel data was successful.")
except Exception as e:
    print(f"An error occurred while scraping YouTube channel data: {e}")

client = commands.Bot(command_prefix="!", intents=discord.Intents.all(), help_command=None, status=discord.Status.online, activity=discord.Activity(type=discord.ActivityType.playing, name="/help"), application_id=config["client_id"])

def sticky_ready(id, content):
    @tasks.loop(seconds=12)
    async def stickyloop(channel: discord.TextChannel, message: str):
        if channel.id not in client.sticky or client.sticky[channel.id] != message: stickyloop.stop()
        elif message not in [msg.content async for msg in channel.history(limit=20, oldest_first=False)]: await channel.send(f"{message}")
    client.sticky[id] = content; stickyloop.start(client.get_channel(id), content)
    print("Sticky message loop started.")

@client.event
async def on_ready():
    print(f"\033[92m[!]\033[0m \033[94m{time.strftime('%Y-%m-%d - %H:%M')}: Initiating bot. Please wait...\033[0m", end='', flush=True)
    print("\n\033[92m[!]\033[0m \033[94mBot is online\033[0m")
    print(f"\033[92m[!]\033[0m \033[94mLogged in as: {client.user} - {client.user.id}\033[0m")
    conn = sqlite3.connect(f"sticky.db")
    cursor = conn.cursor()
    values = cursor.execute("SELECT * FROM infos_salons").fetchall()
    print(values)
    for i in values:
        if i[1] != "": sticky_ready(i[0], i[1])
    conn = sqlite3.connect('Data/user.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM roles')
    values = cursor.fetchall()
    print(values)
    try:
        for i in values: client.add_view(mAddBtn(content=i[4], emoji=i[3], role=discord.Object(id=i[2])))
        print("Added view to client.")
    except Exception as e: print(e)

@tasks.loop(seconds=30)
async def checker():
    print("Running checker...")
    conn = sqlite3.connect(f"Data/users.db")
    curs = conn.cursor()
    curs.execute(f"SELECT id, channel, message FROM giveaways WHERE ends<={int(str(time.time()).split('.')[0])} AND ended=0")
    for giveawayid, channelid, messageid in curs.fetchall():
        curs.execute(f"""UPDATE giveaways SET (ended) = (1) WHERE id={giveawayid}""")
        conn.commit()
        channel = client.get_channel(channelid)
        if channel is None or (message := await channel.fetch_message(messageid)) is None or "Giveaway ended" in message.embeds[0].description: continue
        prize = message.embeds[0].title
        winners = int(message.embeds[0].description.split("Winners:** ")[1].split("**Ends")[0].replace("\n", "").replace(r"\n", ""))
        choices = [user async for r in message.reactions if r.emoji == "🎉" for user in r.users() if user.id != client.user.id]
        if len(choices) < winners: await message.reply(f"Not enough participants for this giveaway."); return
        winnerz = str([winner.mention for winner in random.choices(choices, k=winners)]).replace("[", "").replace("]", "").replace("'", "")
        ember = message.embeds[0]
        ember.description = f'{message.embeds[0].description.split("React with")[0]}Giveaway ended.'
        await message.edit(embed=ember)
        emb = discord.Embed(title=prize, colour=discord.Colour.green())
        emb.add_field(name="Winners", value=winnerz, inline=False)
        emb.set_footer(text="Giveaway ended")
        await message.reply(embed=emb)
    print("Giveaway check completed.")

@tasks.loop(seconds=60)
async def twitchloop():
    print("Running twitchloop...")
    if (channel := client.get_channel(twitchid)) is None: return print("Invalid channel configured.")
    rs = requests.Session()
    r = rs.post('https://id.twitch.tv/oauth2/token', {'client_id': clientid, 'client_secret': clientsecret, "grant_type": 'client_credentials'})
    token = r.json()['access_token']
    for friend_twitch_channel in ["sirlygophobia"]:
        req = requests.get(f"https://api.twitch.tv/helix/streams?user_login={friend_twitch_channel}", headers={'Client-ID': clientid, 'Authorization': 'Bearer ' + token})
        if len((res := req.json())['data']) > 0 and (streamid := res['data'][0]["id"]) not in notified:
            notified.append(streamid)
            game_name = res['data'][0]["game_name"]
            print(f"Debug - Twitch API Data (Friend): {res['data'][0]}")
            message = f"**'{friend_twitch_channel}' is Live**\n🚨https://www.twitch.tv/{friend_twitch_channel} 🚨" + (f"\nPlaying: {game_name}" if game_name else "") + " 👍"
            await channel.send(message)
            print(f"Twitch API Status Code: {req.status_code}")
            print(f"Twitch API Response: {req.text}")

@tasks.loop(seconds=60)
async def youtubeloop():
    print("Running youtubeloop...")
    try:
        if (channel := client.get_channel(youtubeid)) is None: return print("Invalid channel configured.")
        for results in [scrapetube.get_channel(ytchannel, sort_by="newest", limit=2, content_type=ctype) for ctype in ["videos", "shorts", "streams"]]:
            for result in results:
                if result['videoId'] not in previous:
                    previous.append(result['videoId'])
                    await channel.send(f"**{channel.guild.default_role} New Upload**\nhttps://www.youtube.com/watch?v={result['videoId']}")
                    print(f"New upload: https://www.youtube.com/watch?v={result['videoId']}")
    except Exception as exc: print(f"Error: {exc}")

@client.event
async def on_guild_join(guild: discord.Guild): 
    print("Bot joined a new guild...")
    await client.tree.sync(guild=guild)

@client.event
async def on_member_join(member: discord.Member):
    print(f"New member joined: {member.name}")
    if (welcome := client.get_channel(welcomeid)) is None: return
    guild = member.guild
    embed = discord.Embed(title=f"**╭━━━━━✦WELCOME✦━━━━━━━━━━━━━━━━➧**", colour=client.colour).add_field(name="", value=f"<a:green_crown_sparkle:1105696367667597372> Hello <@{member.id}> <a:green_crown_sparkle:1105696367667597372>", inline=False).add_field(name="", value=f"<a:green_online:1105696576350978111> Welcome to **{guild.name}** <a:green_online:1105696576350978111>", inline=False).add_field(name="<a:green_heartstatic:1108584890305351731> Your presence is a valuable addition <a:green_heartstatic:1108584890305351731>", value=f"**━━━━━━━━━━━✦INFO✦━━━━━━━━━━━━━━━━➧**\n<a:green_planet:1105696371631202344> Read our Rules here <#1042619540774846605>\n<a:green_planet:1105696371631202344>  For Help, open a <#1105676532095127643>\n<a:green_planet:1105696371631202344> Customize Your Profile <#1105673962647715951> \n**╰━━━━━━✦ENJOY✦━━━━━━━━━━━━━━━━━━➧**", inline=False)

@client.event
async def on_member_remove(member: discord.Member):
    print(f"Member left: {member.name}")
    if (channel := client.get_channel(welcomeid)) is None: return
    emb = discord.Embed(title="Goodbye from the server!", description=f"{member.mention} has left {member.guild.name}.", color=discord.Color.red())
    emb.set_thumbnail(url=member.avatar_url)
    await channel.send(embed=emb)

@client.event
async def on_message(message):
    print(f"Received a message from {message.author.name}")
    if message.author.bot or message.content.startswith("!"): return
    if isinstance(message.channel, discord.DMChannel) and message.author.id != 1039329011173699734:
        print("Processing a direct message...")
        emb = discord.Embed(title="Modmail", description=message.content, color=discord.Color.green())
        emb.set_author(name=message.author, icon_url=message.author.avatar_url)
        if (channel := client.get_channel(modmailid)) is not None: await channel.send(embed=emb); await message.add_reaction("✅")
    elif isinstance(message.channel, discord.TextChannel) and message.channel.id == modmailid and not message.content.startswith("<@"):
        print("Processing a message in a text channel...")
        emb = discord.Embed(title="Modmail", description=message.content, color=discord.Color.green())
        emb.set_author(name=message.author, icon_url=message.author.avatar_url)
        if (user := client.get_user(int(message.content.split(" ")[0]))) is not None: await user.send(embed=emb); await message.add_reaction("✅")

@client.event
async def on_guild_channel_delete(channel):
    print("A guild channel was deleted...")
    conn = sqlite3.connect(f"sticky.db")
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM infos_salons WHERE id={channel.id}")
    conn.commit()
    conn.close()

@client.event
async def on_guild_channel_create(channel):
    print("A guild channel was created...")
    conn = sqlite3.connect(f"sticky.db")
    cursor = conn.cursor()
    cursor.execute(f"INSERT INTO infos_salons (id, message) VALUES ({channel.id}, '')")
    conn.commit()
    conn.close()

@client.event
async def on_guild_channel_update(before, after):
    print("A guild channel was updated...")
    conn = sqlite3.connect(f"sticky.db")
    cursor = conn.cursor()
    cursor.execute(f"UPDATE infos_salons SET id={after.id} WHERE id={before.id}")
    conn.commit()
    conn.close()

@client.event
async def on_guild_update(before, after):
    print("A guild was updated...")
    conn = sqlite3.connect(f"sticky.db")
    cursor = conn.cursor()
    cursor.execute(f"UPDATE infos_salons SET id={after.system_channel.id} WHERE id={before.system_channel.id}")
    conn.commit()
    conn.close()

@client.event
async def setup_hook():
    print("Setting up the hook...")
    print(f"\033[92m[!]\033[0m \033[94mSynced\033[0m \033[92m{len(await client.tree.sync())}\033[0m \033[94mcommands\033[0m")
    try:
        conn = sqlite3.connect(f"Data/users.db")
        curs = conn.cursor()
        for run in ["CREATE TABLE IF NOT EXISTS users (userid integer PRIMARY KEY, balance integer, invited integer, left integer, voice integer DEFAULT 0);", "CREATE TABLE IF NOT EXISTS warnings (userid integer PRIMARY KEY, reason varchar, warner integer);", "CREATE TABLE IF NOT EXISTS giveaways (id integer, ends timestamp, channel integer, message integer, ended integer);"]: curs.execute(run)
        conn.commit()
        conn.close()
        print("\033[92m[!]\033[0m \033[94mUsers Database Connected\033[0m")
    except Exception as exc: print(exc), quit()

async def loadcogs(): 
    print("Loading cogs...")
    [await client.load_extension(f'Commands.{files[:-3]}') for files in os.listdir(f'Commands') if files.endswith(".py")]

async def startup():
    print("Starting up...")
    async with client:
        client.sticky, client.colour, client.greenline, client.modmailid = {}, discord.Colour.from_rgb(101, 255, 0), "https://i.ibb.co/BVTKyXb/greenline.gif", modmailid
        await loadcogs()
        await client.start(token)

asyncio.run(startup())

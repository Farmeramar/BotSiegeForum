import os
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
FORUM_CHANNEL_ID = int(os.getenv('FORUM_CHANNEL_ID'))
OUTPUT_CHANNEL_ID = int(os.getenv('OUTPUT_CHANNEL_ID'))
MESSAGE_ID_FILE = "message_id.txt"

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.messages = True
intents.presences = False

bot = commands.Bot(command_prefix="!", intents=intents)

def save_message_id(msg_id):
    with open(MESSAGE_ID_FILE, "w") as f:
        f.write(str(msg_id))

def load_message_id():
    if not os.path.isfile(MESSAGE_ID_FILE):
        return None
    with open(MESSAGE_ID_FILE, "r") as f:
        return int(f.read().strip())

async def count_posts_with_screenshots(thread):
    messages = [m async for m in thread.history(limit=100, oldest_first=True)]
    
    # Skip the first message (index 0) and only count posts with attachments (screenshots)
    posts_with_screenshots = 0
    
    for i, msg in enumerate(messages):
        if i == 0:  # Skip the first message
            continue
        
        # Check if message has attachments (screenshots/images)
        if msg.attachments:
            # Check if any attachment is an image
            for attachment in msg.attachments:
                if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp']):
                    posts_with_screenshots += 1
                    break  # Count this message only once even if it has multiple images
    
    return posts_with_screenshots


@bot.event
async def on_ready():
    print(f"Eingeloggt als {bot.user}")
    update_forum_overview.start()


@tasks.loop(minutes=1)
async def update_forum_overview():
    await bot.wait_until_ready()
    forum_channel = bot.get_channel(FORUM_CHANNEL_ID)
    output_channel = bot.get_channel(OUTPUT_CHANNEL_ID)

    threads = list(forum_channel.threads)

    archived = []
    async for thread in forum_channel.archived_threads(limit=None):
        archived.append(thread)

    all_threads = threads + archived

    if not all_threads:
        content = "⚠️ Es gibt derzeit keine Forum-Einträge."
    else:
        # Separate threads into Bedingungen and Clanmember categories
        bedingungen_threads = []
        clanmember_threads = []
        
        for thread in all_threads:
            if "Bedingung" in thread.name:
                bedingungen_threads.append(thread)
            else:
                clanmember_threads.append(thread)
        
        content = ""
        
        # Overview Bedingungen section
        if bedingungen_threads:
            content += "**📋 Overview Bedingungen:**\n\n"
            for thread in bedingungen_threads:
                count = await count_posts_with_screenshots(thread)
                content += f"- [{thread.name}]({thread.jump_url}) ({count} Beiträge)\n"
            content += "\n"
        
        # Overview Clanmember section
        if clanmember_threads:
            content += "**👥 Overview Clanmember:**\n\n"
            for thread in clanmember_threads:
                author = thread.owner.display_name if thread.owner else "Unbekannt"
                count = await count_posts_with_screenshots(thread)
                content += f"- [{thread.name}]({thread.jump_url}) von {author} ({count} Beiträge)\n"
            content += "\n"

        content += f"*Letzte Aktualisierung: {datetime.utcnow().strftime('%d.%m.%Y %H:%M:%S')} UTC*"

    message_id = load_message_id()

    if message_id:
        try:
            msg = await output_channel.fetch_message(message_id)
            await msg.edit(content=content)
            return
        except discord.NotFound:
            pass

    msg = await output_channel.send(content)
    save_message_id(msg.id)


@bot.command()
async def update(ctx):
    await update_forum_overview()
    await ctx.send("✅ Forum-Übersicht aktualisiert.")

bot.run(TOKEN)

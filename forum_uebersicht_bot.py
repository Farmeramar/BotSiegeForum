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

async def count_logical_posts(thread, window_minutes=10):
    messages = [m async for m in thread.history(limit=100, oldest_first=True)]

    logical_posts = 0
    last_author = None
    last_time = None

    for msg in messages:
        if msg.author != last_author:
            logical_posts += 1
        elif last_time and (msg.created_at - last_time).total_seconds() > window_minutes * 60:
            logical_posts += 1

        last_author = msg.author
        last_time = msg.created_at

    return logical_posts


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
        content = "**📌 Übersicht der Forum-Einträge:**\n\n"
        for thread in all_threads:
            author = thread.owner.display_name if thread.owner else "Unbekannt"
            count = await count_logical_posts(thread)
            content += f"- [{thread.name}]({thread.jump_url}) von {author} ({count} Beiträge)\n"

        content += f"\n*Letzte Aktualisierung: {datetime.utcnow().strftime('%d.%m.%Y %H:%M:%S')} UTC*"

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

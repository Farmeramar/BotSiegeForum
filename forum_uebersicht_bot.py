import os
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
FORUM_CHANNEL_ID = int(os.getenv('FORUM_CHANNEL_ID'))
OUTPUT_CHANNEL_ID = int(os.getenv('OUTPUT_CHANNEL_ID'))

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

CATEGORIES = {
    "🛡️ Allianzen / Fraktionen": ["bannerlords", "hochelfen", "dunkelelfen", "ork", "untot", "liga", "pakt", "union", "barbaren", "sumpfteufel"],
    "✨ Affinitäten": ["magie", "kraft", "void", "seele"],
    "📊 Rollen / Seltenheit": ["ang", "def", "lp", "unterstützer", "legendär", "episch", "selten"]
}

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
    print(f"✅ Eingeloggt als {bot.user}")
    update_forum_overview.start()

@tasks.loop(minutes=5)
async def update_forum_overview():
    print("🔁 update_forum_overview läuft...")
    forum_channel = bot.get_channel(FORUM_CHANNEL_ID)
    output_channel = bot.get_channel(OUTPUT_CHANNEL_ID)

    threads = list(forum_channel.threads)

    archived = []
    async for thread in forum_channel.archived_threads(limit=None):
        archived.append(thread)

    all_threads = threads + archived

    grouped = {key: [] for key in CATEGORIES}
    ungrouped = []

    for thread in all_threads:
        title = thread.name.lower()
        matched = False
        for group, keywords in CATEGORIES.items():
            if any(kw in title for kw in keywords):
                grouped[group].append(thread)
                matched = True
                break
        if not matched:
            ungrouped.append(thread)

    content = f"**📌 Thematische Übersicht ({len(all_threads)} Einträge):**\n\n"

    for category, thread_list in grouped.items():
        content += f"{category}\n"
        if not thread_list:
            content += "_Keine Einträge_\n"
        for thread in thread_list:
            count = await count_logical_posts(thread)
            owner = thread.owner.display_name if thread.owner else "Unbekannt"
            content += f"• [{thread.name}]({thread.jump_url}) von {owner} ({count})\n"
        content += "\n"

    if ungrouped:
        content += "👥 **Beiträge der Clanmitglieder**\n"
        for thread in ungrouped:
            count = await count_logical_posts(thread)
            owner = thread.owner.display_name if thread.owner else "Unbekannt"
            content += f"• [{thread.name}]({thread.jump_url}) von {owner} ({count})\n"
        content += "\n"

    content += f"*Letzte Aktualisierung: {datetime.now(timezone.utc).strftime('%d.%m.%Y %H:%M:%S')} UTC*"

    await output_channel.send(content)

@bot.command()
async def update(ctx):
    await update_forum_overview()
    await ctx.send("✅ Übersicht manuell aktualisiert.")

bot.run(TOKEN)

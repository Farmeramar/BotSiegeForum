import os
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
FORUM_CHANNEL_ID = int(os.getenv("FORUM_CHANNEL_ID"))
OUTPUT_CHANNEL_ID = int(os.getenv("OUTPUT_CHANNEL_ID"))

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

overview_message_id = None

async def count_all_posts(thread):
    return sum(1 async for _ in thread.history(limit=None))

@bot.event
async def on_ready():
    print(f"✅ Eingeloggt als {bot.user}")
    await load_existing_message()
    update_forum_overview.start()

async def load_existing_message():
    global overview_message_id
    output_channel = bot.get_channel(OUTPUT_CHANNEL_ID)
    async for msg in output_channel.history(limit=20):
        if msg.author == bot.user and "Thematische Übersicht" in msg.content:
            overview_message_id = msg.id
            print(f"🔁 Bestehende Übersicht gefunden: {msg.id}")
            break

@tasks.loop(minutes=5)
async def update_forum_overview():
    global overview_message_id
    print("🔄 update_forum_overview läuft...")

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

    content = f"**📌 Thematische Übersicht ({len(all_threads)} Einträge):**\\n\\n"

    for category, thread_list in grouped.items():
        content += f"{category}\\n"
        if not thread_list:
            content += "_Keine Einträge_\\n"
        for thread in thread_list:
            count = await count_all_posts(thread)
            owner = thread.owner.display_name if thread.owner else "Unbekannt"
            content += f"• [{thread.name}]({thread.jump_url}) von {owner} ({count})\\n"
        content += "\\n"

    if ungrouped:
        content += "👥 **Beiträge der Clanmitglieder**\\n"
        for thread in ungrouped:
            count = await count_all_posts(thread)
            owner = thread.owner.display_name if thread.owner else "Unbekannt"
            content += f"• [{thread.name}]({thread.jump_url}) von {owner} ({count})\\n"
        content += "\\n"

    content += f"*Letzte Aktualisierung: {datetime.now(timezone.utc).strftime('%d.%m.%Y %H:%M:%S')} UTC*"

    # Beitrag bearbeiten oder neu posten
    if overview_message_id:
        try:
            message = await output_channel.fetch_message(overview_message_id)
            await message.edit(content=content)
            print("📝 Übersicht aktualisiert (bearbeitet).")
        except discord.NotFound:
            msg = await output_channel.send(content)
            overview_message_id = msg.id
            print("📌 Neue Übersicht erstellt (vorherige nicht gefunden).")
    else:
        msg = await output_channel.send(content)
        overview_message_id = msg.id
        print("📌 Neue Übersicht erstellt.")

@bot.command()
async def update(ctx):
    await update_forum_overview()
    await ctx.send("✅ Übersicht manuell aktualisiert.")

bot.run(TOKEN)

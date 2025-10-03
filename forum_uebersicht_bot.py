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
    "🛡️ Allianzen / Fraktionen": [
        "bannerlords", "hochelfen", "dunkelelfen", "ork",
        "untot", "liga", "pakt", "union", "barbaren", "sumpfteufel"
    ],
    "✨ Affinitäten": ["magie", "kraft", "void", "seele"],
    "📊 Rollen / Seltenheit": ["ang", "def", "lp", "unterstützer", "legendär", "episch", "selten"]
}

# Merkt sich die ID des zuletzt geposteten Übersicht-Posts
overview_message_id = None

# Neue, korrigierte Zählfunktion: zählt **alle Nachrichten**
async def count_all_posts(thread):
    count = 0
    async for msg in thread.history(limit=None):
        has_image_attachment = any(
            a.content_type and a.content_type.startswith("image/") for a in msg.attachments
        )
        has_image_embed = any(e.image for e in msg.embeds)

        if has_image_attachment or has_image_embed:
            count += 1
    return count

@bot.event
async def on_ready():
    print(f"✅ Eingeloggt als {bot.user}")
    await load_existing_message()
    update_forum_overview.start()

# Prüft beim Start, ob schon eine Übersicht existiert
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

    # Threads kategorisieren
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

    # Übersichtstext bauen
    content = f"**📌 Thematische Übersicht ({len(all_threads)} Einträge):**\n\n"

    for category, thread_list in grouped.items():
        content += f"{category}\n"
        if not thread_list:
            content += "_Keine Einträge_\n"
        for thread in thread_list:
            count = await count_all_posts(thread)
            owner = thread.owner.display_name if thread.owner else "Unbekannt"
            content += f"• [{thread.name}]({thread.jump_url}) von {owner} ({count})\n"
        content += "\n"

    if ungrouped:
        content += "👥 **Beiträge der Clanmitglieder**\n"
        for thread in ungrouped:
            count = await count_all_posts(thread)
            owner = thread.owner.display_name if thread.owner else "Unbekannt"
            content += f"• [{thread.name}]({thread.jump_url}) von {owner} ({count})\n"
        content += "\n"

    content += f"*Letzte Aktualisierung: {datetime.now(timezone.utc).strftime('%d.%m.%Y %H:%M:%S')} UTC*"

    # Übersicht bearbeiten oder neu erstellen
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

# Manuelles Update über !update
@bot.command()
async def update(ctx):
    await update_forum_overview()
    await ctx.send("✅ Übersicht manuell aktualisiert.")

bot.run(TOKEN)

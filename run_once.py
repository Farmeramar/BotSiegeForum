import os
import discord
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN") or os.getenv("DISCORD_TOKEN".replace("TOKEN", "BOT_TOKEN"))  # optional fallback
# Ich empfehle diese Namen:
# DISCORD_TOKEN, FORUM_CHANNEL_ID, OUTPUT_CHANNEL_ID

TOKEN = os.getenv("DISCORD_TOKEN") or os.getenv("DISCORD_BOT_TOKEN") or os.getenv("DISCORD_TOKEN")
FORUM_CHANNEL_ID = int(os.getenv("FORUM_CHANNEL_ID"))
OUTPUT_CHANNEL_ID = int(os.getenv("OUTPUT_CHANNEL_ID"))

# Intents minimal halten (du brauchst keine message_content / members)
intents = discord.Intents.default()
intents.guilds = True

client = discord.Client(intents=intents)

CATEGORIES = {
    "🛡️ Allianzen / Fraktionen": [
        "bannerlords", "hochelfen", "dunkelelfen", "ork",
        "untot", "liga", "pakt", "union", "barbaren", "sumpfteufel"
    ],
    "✨ Affinitäten": ["magie", "kraft", "void", "seele"],
    "📊 Rollen / Seltenheit": ["ang", "def", "lp", "unterstützer", "legendär", "episch", "selten"]
}

async def count_all_posts(thread: discord.Thread) -> int:
    count = 0
    async for msg in thread.history(limit=None):
        has_image_attachment = any(
            a.content_type and a.content_type.startswith("image/") for a in msg.attachments
        )
        has_image_embed = any(e.image for e in msg.embeds)
        if has_image_attachment or has_image_embed:
            count += 1
    return count

async def find_existing_overview_message(output_channel: discord.TextChannel):
    async for msg in output_channel.history(limit=50):
        if msg.author == client.user and msg.content and "Thematische Übersicht" in msg.content:
            return msg
    return None

async def build_and_post_overview():
    forum_channel = await client.fetch_channel(FORUM_CHANNEL_ID)
    output_channel = await client.fetch_channel(OUTPUT_CHANNEL_ID)

    if not isinstance(forum_channel, discord.ForumChannel):
        raise RuntimeError("FORUM_CHANNEL_ID ist kein Forum-Channel.")

    # Aktive + archivierte Threads sammeln
    threads = list(forum_channel.threads)

    archived = []
    async for thread in forum_channel.archived_threads(limit=None):
        archived.append(thread)

    all_threads = threads + archived

    grouped = {key: [] for key in CATEGORIES}
    ungrouped = []

    for thread in all_threads:
        title = (thread.name or "").lower()
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
            content += f"• [{thread.name}]({thread.jump_url}) ({count})\n"
        content += "\n"

    if ungrouped:
        content += "👥 **Beiträge der Clanmitglieder**\n"
        for thread in ungrouped:
            count = await count_all_posts(thread)
            owner = "Unbekannt"
            if thread.owner:
                owner = thread.owner.display_name
            elif getattr(thread, "owner_id", None):
                owner = f"User {thread.owner_id}"
            content += f"• [{thread.name}]({thread.jump_url}) von {owner} ({count})\n"
        content += "\n"

    content += f"*Letzte Aktualisierung: {datetime.now(timezone.utc).strftime('%d.%m.%Y %H:%M:%S')} UTC*"

    existing = await find_existing_overview_message(output_channel)
    if existing:
        await existing.edit(content=content)
        print("📝 Übersicht aktualisiert (bearbeitet).")
    else:
        await output_channel.send(content)
        print("📌 Neue Übersicht erstellt.")

@client.event
async def on_ready():
    try:
        print(f"✅ Eingeloggt als {client.user}")
        await build_and_post_overview()
    finally:
        await client.close()

if __name__ == "__main__":
    if not TOKEN:
        raise RuntimeError("DISCORD_TOKEN / DISCORD_BOT_TOKEN fehlt.")
    client.run(TOKEN)

import os
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
FORUM_CHANNEL_ID = int(os.getenv('FORUM_CHANNEL_ID'))
OUTPUT_CHANNEL_ID = int(os.getenv('OUTPUT_CHANNEL_ID'))

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.messages = True
intents.presences = False

bot = commands.Bot(command_prefix="!", intents=intents)

message_id = None  # Übersichtsnachricht-ID


@bot.event
async def on_ready():
    print(f"✅ Eingeloggt als {bot.user}")
    update_forum_overview.start()


@tasks.loop(minutes=5)
async def update_forum_overview():
    await bot.wait_until_ready()
    forum_channel = bot.get_channel(FORUM_CHANNEL_ID)
    output_channel = bot.get_channel(OUTPUT_CHANNEL_ID)

    threads = await forum_channel.active_threads()
    archived = await forum_channel.archived_threads().flatten()
    all_threads = threads + archived

    if not all_threads:
        content = "⚠️ Es gibt derzeit keine Forum-Einträge."
    else:
        content = "**📌 Übersicht der Forum-Einträge:**\n\n"
        for thread in all_threads:
            author = thread.owner.display_name if thread.owner else "Unbekannt"
            content += f"- [{thread.name}]({thread.jump_url}) von {author}\n"

    global message_id
    if message_id:
        try:
            msg = await output_channel.fetch_message(message_id)
            await msg.edit(content=content)
            return
        except discord.NotFound:
            pass

    msg = await output_channel.send(content)
    message_id = msg.id


@bot.command()
async def update(ctx):
    await update_forum_overview()
    await ctx.send("✅ Forum-Übersicht aktualisiert.")

bot.run(TOKEN)

# Discord Forum Overview Bot

## Overview
This is a Discord bot that monitors forum threads in a specified Discord forum channel and provides automated overview updates. The bot tracks all forum posts, counts logical posts per thread, and maintains an up-to-date summary in a designated output channel.

## Current State
- ✅ **Running Successfully**: Bot is connected and operational
- ✅ **Dependencies Installed**: discord.py and python-dotenv are installed
- ✅ **Environment Configured**: Discord credentials are set via Replit Secrets
- ✅ **Workflow Active**: Bot runs continuously via Python workflow
- ✅ **Deployment Ready**: Configured for VM deployment to maintain persistent connection

## User Preferences
- Language: German (bot messages are in German)
- Update frequency: Every 1 minute
- Logical post counting: Groups messages from same author within 10-minute windows

## Project Architecture

### Core Files
- `forum_uebersicht_bot.py`: Main bot application with Discord.py integration
- `requirements.txt`: Python dependencies (discord.py, python-dotenv)
- `message_id.txt`: Auto-generated file to track the overview message ID for editing
- `.gitignore`: Standard Python gitignore with bot-specific exclusions

### Key Features
1. **Forum Monitoring**: Continuously monitors specified forum channel for new threads
2. **Thread Overview**: Generates formatted overview of all active and archived threads
3. **Message Editing**: Updates existing overview message instead of posting new ones
4. **Logical Post Counting**: Counts meaningful posts per thread (groups rapid messages from same user)
5. **Manual Updates**: Provides `!update` command for immediate refresh

### Environment Variables
- `DISCORD_TOKEN`: Bot authentication token
- `FORUM_CHANNEL_ID`: ID of the Discord forum channel to monitor
- `OUTPUT_CHANNEL_ID`: ID of the channel where overviews are posted

### Deployment Configuration
- **Target**: VM (Virtual Machine) for persistent connection
- **Runtime**: Python 3.11 with discord.py
- **Startup**: `python forum_uebersicht_bot.py`

## Recent Changes (September 11, 2025)
- Initial project setup in Replit environment
- Installed Python 3.11 and required dependencies
- Configured environment variables via Replit Secrets
- Set up continuous workflow for bot operation
- Configured VM deployment for production use
- Bot successfully connected to Discord as "Siege Forum#7646"

## Usage
The bot runs automatically and updates the forum overview every minute. Users can also trigger manual updates using the `!update` command in Discord. The bot will create and maintain a single overview message in the designated output channel, editing it rather than creating new messages.
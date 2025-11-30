# Ice Skating Telegram Bot (Конькобежец Бот)

## Overview
A Telegram bot about speed skating (конькобежный спорт) that provides information about Russian and international skaters, world records, and legendary ice rinks. The bot includes a "Spy" game mode based on speed skating locations.

**Current State**: Running and configured for the Replit environment.

**Technology Stack**: 
- Python 3.11
- aiogram 3.13.1 (Telegram Bot framework)
- Async/await pattern with asyncio

## Recent Changes
- **Nov 29, 2025**: Initial import from GitHub and Replit environment setup
  - Installed Python 3.11 and dependencies
  - Configured BOT_TOKEN secret for Telegram API
  - Created workflow to run the bot
  - Added .gitignore for Python projects
  - Fixed TelegramConflictError by adding webhook deletion on startup (prevents conflicts with other bot instances)
  - Updated all InlineKeyboardButton calls to use keyword arguments (text=) for aiogram 3.13.1 compatibility

## Project Structure
```
.
├── main.py              # Main bot application with all handlers
├── requirements.txt     # Python dependencies (aiogram)
├── render.yaml         # Original Render deployment config (not used in Replit)
└── replit.md           # This documentation file
```

## Bot Features
1. **Spy Game**: Random assignment of spy or location from speed skating venues
2. **Russian Skaters**: Information about top Russian speed skaters
3. **Foreign Skaters**: Information about international speed skating champions
4. **World Records**: Current world records (as of Nov 2025) for various distances
5. **Legendary Venues**: Famous ice skating rinks around the world

## Configuration

### Environment Variables
- `BOT_TOKEN`: Telegram bot token from @BotFather (stored in Replit Secrets)

### Running the Bot
The bot runs automatically via the "Telegram Bot" workflow:
```bash
python main.py
```

The bot uses long polling to receive updates from Telegram and requires an active internet connection.

## Development Notes
- This is a backend-only application (no frontend)
- The bot runs continuously and polls Telegram for messages
- All text and data are in Russian (target audience: Russian-speaking speed skating fans)
- Uses inline keyboard markup for navigation

## Dependencies
- **aiogram**: Modern async Telegram Bot framework
- All dependencies are listed in `requirements.txt`

## User Preferences
- None documented yet

## Architecture Decisions
- **Nov 29, 2025**: Using original project structure with minimal modifications
  - Kept all data structures and handlers as-is from the original import
  - No database required - all data is stored in Python lists
  - Using MemoryStorage for FSM (Finite State Machine) storage

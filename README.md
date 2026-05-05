# Job Agent

Automated job search assistant powered by Claude API and Telegram.

## Features
- Scrape job offers from InfoJobs and LinkedIn
- Filter with Claude AI based on custom criteria
- Interactive Telegram bot for CV generation and analysis
- SQLite database for offer tracking

## Setup
1. python3 -m venv venv
2. source venv/bin/activate (macOS/Linux) or env\Scripts\activate (Windows)
3. pip install -r requirements.txt
4. Create .env with TELEGRAM_BOT_TOKEN, ANTHROPIC_API_KEY, etc.
5. python3 job_scraper.py

## Tech
- Python 3.13+
- Claude API (Haiku 4.5, Sonnet 4.6)
- python-telegram-bot
- feedparser, imap-tools, sqlite3

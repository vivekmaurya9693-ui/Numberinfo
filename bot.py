# bot_simple.py — sirf khud use karne ke liye
import os
import threading
import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
import requests

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
API_URL = os.getenv("API_URL", "http://localhost:10000").rstrip("/")
API_KEY = os.getenv("API_KEY", "").strip()  # tumhari apni key

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


# =========================================================
# START
# =========================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Number Info Bot\n\n"
        "Mujhe koi bhi number ya naam bhejo — main search karunga.\n\n"
        "Example:\n"
        "• 9876543210\n"
        "• Rahul\n"
        "• Delhi"
    )


# =========================================================
# SEARCH
# =========================================================

async def handle_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()

    if not query:
        return

    # "searching..." message
    msg = await update.message.reply_text("🔎 Search kar raha hoon...")

    try:
        response = requests.get(
            f"{API_URL}/api/search",
            params={"query": query, "limit": 10},
            headers={"X-API-Key": API_KEY},
            timeout=15,
        )

        data = response.json()

        # Error handling
        if response.status_code != 200 or not data.get("success"):
            error = data.get("message", "Unknown error")
            await msg.edit_text(f"❌ Error: {error}")
            return

        results = data.get("results", [])
        count = data.get("count", 0)

        if not results:
            await msg.edit_text(f"🔍 '{query}' ke liye kuch nahi mila.")
            return

        # Results format karo
        lines = [f"🔍 *Results for:* `{query}`", f"📊 *Count:* {count}", ""]

        for i, record in enumerate(results[:10], 1):
            lines.append(f"*{i}.*")
            for key, value in record.items():
                if key.startswith("_"):
                    continue
                if value in (None, "", []):
                    continue
                lines.append(f"  • *{key}:* `{value}`")
            lines.append("")

        text = "\n".join(lines)

        # Telegram message limit (4096 chars)
        if len(text) > 4000:
            text = text[:4000] + "\n\n_...truncated_"

        await msg.edit_text(text, parse_mode="Markdown")

    except requests.exceptions.Timeout:
        await msg.edit_text("❌ API timeout. Try again.")
    except Exception as e:
        await msg.edit_text(f"❌ Error: {str(e)}")


# =========================================================
# STATS
# =========================================================

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        response = requests.get(f"{API_URL}/api/stats", timeout=10)
        data = response.json()

        await update.message.reply_text(
            f"📊 *API Stats*\n\n"
            f"Status: {data.get('status', '?')}\n"
            f"Version: {data.get('version', '?')}\n"
            f"JSON files: {data.get('json_files', 0)}\n"
            f"TXT files: {data.get('txt_files', 0)}\n"
            f"Total records: {data.get('total_records', 0)}",
            parse_mode="Markdown",
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


# =========================================================
# MAIN
# =========================================================

def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN missing")
    if not API_KEY:
        raise RuntimeError("API_KEY missing")

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search)
    )

    print("Bot chal raha hai...")
    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()

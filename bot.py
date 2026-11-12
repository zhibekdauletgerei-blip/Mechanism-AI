import asyncio
import os
from urllib.parse import urlencode

from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.environ["BOT_TOKEN"]
PUBLIC_URL = os.environ["PUBLIC_URL"].rstrip("/")
PORT = int(os.environ.get("PORT", "8080"))

def app_url(mode="auto", mechanism=""):
    query = urlencode({"mode": mode, "mechanism": mechanism})
    return f"{PUBLIC_URL}/?{query}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🤖 Автоматты құрастыру", web_app=WebAppInfo(url=app_url("auto")))],
        [InlineKeyboardButton("📐 Параметр арқылы құрастыру", web_app=WebAppInfo(url=app_url("params")))],
    ]
    await update.effective_message.reply_text(
        "⚙️ Mechanism AI\n\n"
        "Механизм атауын жазыңыз немесе құрастыру режимін таңдаңыз.\n"
        "Модель Telegram ішіндегі интерактивті терезеде ашылады.",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "Қолдану:\n"
        "1) Механизм атауын жазыңыз (мысалы, «төрт буынды механизм»).\n"
        "2) «Механизмді ашу» батырмасын басыңыз.\n"
        "3) Қозғалысты іске қосыңыз немесе параметрлерді өзгертіңіз.\n\n"
        "Параметрлік режимде буын ұзындықтары мен бастапқы бұрышты өзіңіз енгізе аласыз."
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.effective_message.text or "").strip()
    if not text:
        return
    keyboard = [[InlineKeyboardButton(
        "⚙️ Механизмді құрастыру",
        web_app=WebAppInfo(url=app_url("auto", text)),
    )]]
    await update.effective_message.reply_text(
        f"Сұраныс: «{text}»\n\n"
        "Сәйкес үлгіні ашу үшін төмендегі батырманы басыңыз.",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

async def index(request):
    return web.FileResponse("web/index.html")

async def health(request):
    return web.json_response({"status": "ok", "app": "Mechanism AI"})

async def main():
    bot = Application.builder().token(BOT_TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler("help", help_command))
    bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    await bot.initialize()
    await bot.start()
    await bot.updater.start_polling(drop_pending_updates=True)

    webapp = web.Application()
    webapp.router.add_get("/", index)
    webapp.router.add_get("/health", health)

    runner = web.AppRunner(webapp)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"Mechanism AI web server started on port {PORT}")

    try:
        await asyncio.Event().wait()
    finally:
        await bot.updater.stop()
        await bot.stop()
        await bot.shutdown()
        await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())

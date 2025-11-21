import asyncio
import os
import logging
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from aiohttp import web
import aiohttp

# --- تنظیمات ---
BOT_TOKEN = "8334390292:AAG72ghgfOz85zOH3WrK7-2_rW6tx41yLVs"
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"https://grokbot-1dwv.onrender.com{WEBHOOK_PATH}"
WALLET_ADDRESS = "TPSoFC1qUmzCt7ukgGAMnYwW1CUJeZhiU7"
USDT_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"  # USDT TRC20
MIN_AMOUNT = 29_000_000  # 29 USDT = 29,000,000 SUN
PDF_PATH = "prompts.pdf"

# --- راه‌اندازی ---
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
paid_users = set()

WELCOME_MSG = """
🤖 Welcome!  
You’ve found the ultimate prompt pack for AI-driven SaaS founders.

📘 100 Grok-4 Prompts to Build $1M SaaS Ideas  
→ Reverse-engineered from real $1M+ AI startups  
→ Includes niche, pricing model, defensibility & GTM  
→ Ready to use with Grok, Claude, or ChatGPT

💰 Price: $29 (or 29 USDT)

📥 How to buy:  
1️⃣ Send 29 USDT (on TRC20 network) to:  
👉 TPSoFC1qUmzCt7ukgGAMnYwW1CUJeZhiU7  
2️⃣ Forward your transaction screenshot here  
3️⃣ Get your PDF instantly!

🔒 No middleman • Direct from creator • 100% secure
"""


@dp.message(Command("start"))
async def send_welcome(message: Message):
    user_id = message.from_user.id
    if user_id in paid_users:
        await send_pdf(user_id)
    else:
        await message.answer(WELCOME_MSG)


async def send_pdf(user_id: int):
    try:
        with open(PDF_PATH, "rb") as pdf:
            await bot.send_document(user_id, pdf)
        paid_users.add(user_id)
        logging.info(f"✅ PDF sent to user {user_id}")
    except FileNotFoundError:
        logging.error(f"❌ File '{PDF_PATH}' not found! Make sure it's in the repo root.")
        await bot.send_message(user_id, "⚠️ Sorry, the product file is missing. Please contact support.")
    except Exception as e:
        logging.error(f"❌ Failed to send PDF to {user_id}: {e}")


# --- اسکنر تراکنش TRON (با مدیریت صحیح session) ---
async def monitor_transactions():
    url = f"https://api.trongrid.io/v1/accounts/{WALLET_ADDRESS}/transactions/trc20"
    sent_txs = set()
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers={"Accept": "application/json"}) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for tx in data.get("data", []):
                            tx_id = tx["transaction_id"]
                            if tx_id in sent_txs:
                                continue
                            if (
                                tx["contract_address"].lower() == USDT_CONTRACT.lower()
                                and int(tx["value"]) >= MIN_AMOUNT
                            ):
                                sent_txs.add(tx_id)
                                logging.info(f"✅ Valid payment received: {tx_id}")
        except Exception as e:
            logging.error(f"Scanner error: {e}")
        await asyncio.sleep(30)


# --- Webhook Handlers ---
async def handle_webhook(request: web.Request):
    if request.path == WEBHOOK_PATH:
        try:
            update = await request.json()
            await dp.feed_webhook_update(bot, update)
            return web.Response()
        except Exception as e:
            logging.error(f"Webhook processing error: {e}")
            return web.Response(status=500)
    return web.Response(text="OK")


async def set_webhook_handler(request: web.Request):
    try:
        await bot.set_webhook(WEBHOOK_URL)
        return web.json_response({"success": True, "url": WEBHOOK_URL})
    except Exception as e:
        return web.json_response({"success": False, "error": str(e)}, status=500)


# --- Lifecycle ---
async def on_startup(app: web.Application):
    try:
        await bot.set_webhook(WEBHOOK_URL)
        logging.info("✅ Telegram webhook set successfully")
    except Exception as e:
        logging.error(f"❌ Failed to set webhook: {e}")
    asyncio.create_task(monitor_transactions())
    logging.info("🔄 Transaction scanner started")


async def on_shutdown(app: web.Application):
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("🔌 Webhook removed on shutdown")


# --- اجرای اصلی ---
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    app = web.Application()
    app.router.add_post(WEBHOOK_PATH, handle_webhook)
    app.router.add_get("/", lambda r: web.Response(text="OK"))          # Health check for Render
    app.router.add_get("/setwebhook", set_webhook_handler)            # Manual webhook setup

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    port = int(os.environ.get("PORT", 10000))
    web.run_app(app, host="0.0.0.0", port=port)

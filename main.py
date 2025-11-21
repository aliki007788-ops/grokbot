import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import aiohttp
from aiohttp import web

# --- تنظیمات ---
BOT_TOKEN = "8334390292:AAG72ghgfOz85zOH3WrK7-2_rW6tx41yLVs"  # <<< اینجا توکن رباتت رو جایگزین کن
WALLET_ADDRESS = "TPSoFC1qUmzCt7ukgGAMnYwW1CUJeZhiU7"
USDT_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"  # USDT TRC20
MIN_AMOUNT = 29_000_000  # 29 USDT in SUN (1 USDT = 1,000,000 SUN)
PDF_PATH = "prompts.pdf"

# --- راه‌اندازی ---
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
paid_users = set()

# --- پیام خوش‌آمدگویی ---
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
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    if user_id in paid_users:
        await send_pdf(user_id)
    else:
        await message.answer(WELCOME_MSG)


async def send_pdf(user_id: int):
    try:
        with open(PDF_PATH, "rb") as pdf:
            await bot.send_document(user_id, pdf)
        paid_users.add(user_id)  # جلوگیری از ارسال مکرر
    except Exception as e:
        logging.error(f"Failed to send PDF to {user_id}: {e}")


# --- اسکنر بلاک‌چین TRON ---
async def monitor_transactions():
    url = f"https://api.trongrid.io/v1/accounts/{WALLET_ADDRESS}/transactions/trc20"
    sent_txs = set()

    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers={"Accept": "application/json"}) as resp:
                    if resp.status != 200:
                        logging.warning(f"Trongrid API error: {resp.status}")
                        continue
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
                            sender = tx["from"]
                            logging.info(f"✅ Payment received: {tx_id} from {sender}")
                            # در اینجا نمی‌تونیم کاربر رو مستقیم پیدا کنیم
                            # پس فقط وقتی کاربر /start بزنه و PDF دریافت نکرده باشه، فایل رو می‌دیم
        except Exception as e:
            logging.error(f"Error in transaction monitor: {e}")

        await asyncio.sleep(30)  # هر 30 ثانیه چک بشه


# --- سرور وب ساده برای Render (فقط برای فعال‌کردن Free Tier) ---
async def health_check(request):
    return web.Response(text="OK", content_type="text/plain")


# --- تابع اصلی اجرا ---
async def main():
    logging.basicConfig(level=logging.INFO)

    # راه‌اندازی سرور وب روی پورت مشخص‌شده (Render از متغیر PORT استفاده می‌کنه)
    port = int(os.environ.get("PORT", 10000))
    app = web.Application()
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    logging.info(f"✅ Web server started on port {port}")

    # راه‌اندازی اسکنر بلاک‌چین در پس‌زمینه
    asyncio.create_task(monitor_transactions())

    # راه‌اندازی ربات تلگرام
    logging.info("🤖 Telegram bot is running...")
    await dp.start_polling(bot)


# --- نقطه ورود برنامه ---
if __name__ == "__main__":
    asyncio.run(main())

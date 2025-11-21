# main.py
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import aiohttp
import os

# --- تنظیمات ---
BOT_TOKEN = "8334390292:AAG72ghgfOz85zOH3WrK7-2_rW6tx41yLVs"  # <<< این رو با توکن رباتت جایگزین کن
WALLET_ADDRESS = "TPSoFC1qUmzCt7ukgGAMnYwW1CUJeZhiU7"
USDT_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"  # USDT TRC20
MIN_AMOUNT = 29_000_000  # 29 USDT in SUN (1 USDT = 1,000,000 SUN)
PDF_PATH = "prompts.pdf"  # فایل PDFت رو همین اسم بذار

# --- راه‌اندازی ---
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
paid_users = set()  # کاربرانی که پرداخت کردن

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
        # حذف از لیست برای جلوگیری از ارسال مکرر (اختیاری)
    except Exception as e:
        logging.error(f"Failed to send PDF to {user_id}: {e}")

# --- اسکنر بلاک‌چین ---
async def monitor_transactions():
    url = f"https://api.trongrid.io/v1/accounts/{WALLET_ADDRESS}/transactions/trc20"
    sent_txs = set()
    
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers={"Accept": "application/json"}) as resp:
                    data = await resp.json()
                    for tx in data.get("data", []):
                        tx_id = tx["transaction_id"]
                        if tx_id in sent_txs:
                            continue
                        # بررسی پرداخت USDT
                        if (
                            tx["contract_address"] == USDT_CONTRACT and
                            int(tx["value"]) >= MIN_AMOUNT
                        ):
                            sent_txs.add(tx_id)
                            logging.info(f"Payment received: {tx_id}")
                            # در اینجا می‌تونیم کاربر رو پیدا کنیم، 
                            # ولی چون نمی‌دونیم چه کسی فرستاده، 
                            # فقط وقتی کاربر استارت بزنه PDF می‌فرستیم
        except Exception as e:
            logging.error(f"Error checking transactions: {e}")
        
        await asyncio.sleep(30)  # هر 30 ثانیه چک بشه

# --- راه‌اندازی ---
async def main():
    logging.basicConfig(level=logging.INFO)
    
    # اسکنر رو در پس‌زمینه اجرا کن
    asyncio.create_task(monitor_transactions())
    
    # ربات رو استارت کن
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
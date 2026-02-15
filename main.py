import time
import requests
import pandas as pd
import yfinance as yf
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = "7869743001:AAHu0aBS4w2x244m-YgAcTbKcAhbQNVkGis"

WATCHLIST = set()

# ====== INDICATORS ======
def rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = -delta.where(delta < 0, 0).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def macd(series):
    ema12 = series.ewm(span=12).mean()
    ema26 = series.ewm(span=26).mean()
    macd_line = ema12 - ema26
    signal = macd_line.ewm(span=9).mean()
    return macd_line, signal

# ====== ANALYZE ======
def analyze(symbol):
    df = yf.download(symbol, period="7d", interval="15m", progress=False)
    if df.empty:
        return None

    close = df["Close"]
    rsi_val = rsi(close).iloc[-1]
    macd_line, signal = macd(close)

    msg = f"📊 {symbol}\n"
    msg += f"RSI: {rsi_val:.2f}\n"

    if rsi_val < 30:
        msg += "🟢 RSI quá bán (có thể đảo chiều tăng)\n"
    elif rsi_val > 70:
        msg += "🔴 RSI quá mua (có thể đảo chiều giảm)\n"

    if macd_line.iloc[-1] > signal.iloc[-1] and macd_line.iloc[-2] <= signal.iloc[-2]:
        msg += "🟢 MACD cắt lên\n"
    elif macd_line.iloc[-1] < signal.iloc[-1] and macd_line.iloc[-2] >= signal.iloc[-2]:
        msg += "🔴 MACD cắt xuống\n"

    return msg

# ====== TELEGRAM COMMANDS ======
async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbol = context.args[0].upper()
    WATCHLIST.add(symbol)
    await update.message.reply_text(f"✅ Đã thêm {symbol}")

async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbol = context.args[0].upper()
    WATCHLIST.discard(symbol)
    await update.message.reply_text(f"❌ Đã xoá {symbol}")

async def list_symbols(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📌 Watchlist:\n" + "\n".join(WATCHLIST))

# ====== LOOP ======
async def scan(app):
    while True:
        for s in WATCHLIST:
            result = analyze(s)
            if result:
                await app.bot.send_message(chat_id=CHAT_ID, text=result)
        time.sleep(180)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global CHAT_ID
    CHAT_ID = update.message.chat_id
    await update.message.reply_text("🤖 Bot đã sẵn sàng")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("remove", remove))
    app.add_handler(CommandHandler("list", list_symbols))
    app.run_polling()

if __name__ == "__main__":
    main()

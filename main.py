import asyncio
import time
import yfinance as yf
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = "PUT_TOKEN_VAO_ENV_RENDER"
WATCHLIST = set()
CHAT_ID = None

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

def analyze(symbol):
    df = yf.download(symbol, period="7d", interval="15m", progress=False)
    if df.empty:
        return None

    close = df["Close"]
    rsi_val = rsi(close).iloc[-1]
    macd_line, signal = macd(close)

    msg = f"📊 {symbol}\nRSI: {rsi_val:.2f}\n"

    if rsi_val < 30:
        msg += "🟢 RSI quá bán\n"
    elif rsi_val > 70:
        msg += "🔴 RSI quá mua\n"

    if macd_line.iloc[-1] > signal.iloc[-1]:
        msg += "🟢 MACD bullish\n"
    else:
        msg += "🔴 MACD bearish\n"

    return msg

# ====== COMMANDS ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global CHAT_ID
    CHAT_ID = update.message.chat_id
    await update.message.reply_text("🤖 Bot đã chạy")

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbol = context.args[0].upper()
    WATCHLIST.add(symbol)
    await update.message.reply_text(f"✅ Đã thêm {symbol}")

async def list_symbols(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📌 Watchlist:\n" + "\n".join(WATCHLIST))

# ====== BACKGROUND TASK ======
async def scanner(app):
    while True:
        if CHAT_ID:
            for s in WATCHLIST:
                msg = analyze(s)
                if msg:
                    await app.bot.send_message(chat_id=CHAT_ID, text=msg)
        await asyncio.sleep(180)

# ====== MAIN ======
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("list", list_symbols))

    app.job_queue.run_repeating(
        lambda ctx: asyncio.create_task(scanner(app)),
        interval=180,
        first=10
    )

    app.run_polling()

if __name__ == "__main__":
    main()

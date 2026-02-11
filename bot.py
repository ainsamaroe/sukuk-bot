import os
import requests
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

TOKEN = os.getenv("TOKEN")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

app = Flask(__name__)

# ================= GOOGLE SHEETS =================

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

creds = Credentials.from_service_account_file(
    "credentials.json",
    scopes=scope,
)

client = gspread.authorize(creds)
sheet = client.open_by_key(SPREADSHEET_ID).sheet1

# ================= TELEGRAM =================

telegram_app = ApplicationBuilder().token(TOKEN).build()


# ================= LOGIC =================

def clean_number(text):
    text = str(text).replace("Rp", "").replace(".", "").replace(",", "")
    return float("".join(filter(str.isdigit, text)))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Kirim data seperti:\n\n"
        "PT Nusa, Proyek A, 20-06-2024, 12, 15, 5000000\n\n"
        "Atau kirim foto data."
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        perusahaan, proyek, tgl, tenor, roi, investasi = \
            [x.strip() for x in update.message.text.split(",")]

        tenor = int(tenor)
        roi_value = float(roi) / 100
        investasi = clean_number(investasi)

        proyeksi_margin = (roi_value / 12) * tenor * investasi
        jumlah_sukuk = investasi / 100000

        sheet.append_row([
            datetime.now().strftime("%d/%m/%Y %H:%M"),
            sheet.row_count,
            perusahaan,
            proyek,
            tgl,
            tenor,
            roi,
            investasi,
            jumlah_sukuk,
            round(proyeksi_margin, 2)
        ])

        await update.message.reply_text("✅ Data berhasil disimpan")

    except Exception as e:
        print("ERROR:", e)
        await update.message.reply_text("❌ Format salah atau data tidak valid")


# ================= WEBHOOK =================

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    telegram_app.update_queue.put_nowait(update)
    return "ok"


@app.route("/")
def index():
    return "Bot aktif 24 jam 🚀"


telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

if __name__ == "__main__":
    telegram_app.initialize()
    telegram_app.start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
import telegram
print(telegram.__version__)


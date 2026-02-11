import os
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# ================= ENV =================

TOKEN = os.getenv("TOKEN")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
PORT = int(os.environ.get("PORT", 10000))

if not TOKEN:
    raise ValueError("TOKEN tidak ditemukan di Environment Variables")

if not SPREADSHEET_ID:
    raise ValueError("SPREADSHEET_ID tidak ditemukan di Environment Variables")

# ================= FLASK =================

app = Flask(__name__)

import json

# ================= GOOGLE SHEETS =================

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

google_creds_json = os.getenv("GOOGLE_CREDENTIALS")

if not google_creds_json:
    raise ValueError("GOOGLE_CREDENTIALS tidak ditemukan di Environment Variables")

creds_dict = json.loads(google_creds_json)

creds = Credentials.from_service_account_info(
    creds_dict,
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
        "📌 Kirim data seperti:\n\n"
        "PT Nusa, Proyek A, 20-06-2024, 12, 15, 5000000\n\n"
        "Format:\n"
        "Perusahaan, Proyek, Tanggal, Tenor(bulan), ROI(%), Investasi"
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
            perusahaan,
            proyek,
            tgl,
            tenor,
            roi,
            investasi,
            jumlah_sukuk,
            round(proyeksi_margin, 2)
        ])

        await update.message.reply_text("✅ Data berhasil disimpan ke Google Sheets")

    except Exception as e:
        print("ERROR:", e)
        await update.message.reply_text("❌ Format salah.\nGunakan format:\nPT Nusa, Proyek A, 20-06-2024, 12, 15, 5000000")


# ================= REGISTER HANDLER =================

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))


# ================= WEBHOOK ROUTE =================

@app.route(f"/{TOKEN}", methods=["POST"])
async def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    await telegram_app.process_update(update)
    return "ok"


@app.route("/")
def index():
    return "🚀 Sukuk Bot Aktif 24 Jam"


# ================= START =================

if __name__ == "__main__":
    import asyncio

    async def main():
        await telegram_app.initialize()
        await telegram_app.start()
        await telegram_app.bot.set_webhook(
            url=f"https://{os.getenv('RAILWAY_STATIC_URL')}/{TOKEN}"
        )

    asyncio.run(main())

    app.run(host="0.0.0.0", port=PORT)


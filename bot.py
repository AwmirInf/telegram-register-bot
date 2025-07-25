import logging
import os
import json
from io import StringIO
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, ConversationHandler, filters
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import random
import re

# log
logging.basicConfig(level=logging.INFO)

# Register
(NAME, PHONE, NATIONAL_CODE, FIELD, COMPANIONS, CONFIRM) = range(6)

# Google Sheets
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# JSON from env
SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
credentials_info = json.loads(SERVICE_ACCOUNT_JSON)
credentials = Credentials.from_service_account_info(credentials_info, scopes=SCOPES)

# connect to GoogleSheet
SPREADSHEET_ID = '10pusrlu1RfVkqfjqYoW5IatSO09a5vVxIOySOSZ4nLw'
gc = gspread.authorize(credentials)
worksheet = gc.open_by_key(SPREADSHEET_ID).sheet1

# Start :)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! لطفا نام کامل خود را وارد کنید:")
    return NAME

async def name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text.strip()
    await update.message.reply_text("شماره تماس خود را وارد کنید:")
    return PHONE

async def phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    if not re.fullmatch(r'09\d{9}', phone):
        await update.message.reply_text("❗ شماره تماس معتبر نیست. لطفا با فرمت 09XXXXXXXXX وارد کنید.")
        return PHONE
    context.user_data['phone'] = phone
    await update.message.reply_text("کد ملی خود را وارد کنید:")
    return NATIONAL_CODE

def is_valid_national_code(code):
    if not re.fullmatch(r'\d{10}', code):
        return False
    check = int(code[9])
    s = sum([int(code[i]) * (10 - i) for i in range(9)]) % 11
    return (s < 2 and check == s) or (s >= 2 and check == 11 - s)

async def national_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    if not is_valid_national_code(code):
        await update.message.reply_text("❗ کد ملی معتبر نیست. لطفا دوباره وارد کنید.")
        return NATIONAL_CODE
    context.user_data['national_code'] = code
    await update.message.reply_text("رشته تحصیلی خود را وارد کنید:")
    return FIELD

async def field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['field'] = update.message.text.strip()
    await update.message.reply_text("تعداد همراهان (حداکثر 3 نفر) را وارد کنید:")
    return COMPANIONS

async def companions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        count = int(update.message.text.strip())
        if count < 0 or count > 3:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❗ لطفاً عددی بین 0 تا 3 وارد کنید.")
        return COMPANIONS
    context.user_data['companions'] = count

    text = (
        f"📋 اطلاعات وارد شده:\n"
        f"👤 نام: {context.user_data['name']}\n"
        f"📱 شماره تماس: {context.user_data['phone']}\n"
        f"🆔 کد ملی: {context.user_data['national_code']}\n"
        f"🎓 رشته: {context.user_data['field']}\n"
        f"👥 تعداد همراه: {context.user_data['companions']}\n\n"
        "آیا تایید می‌کنید؟"
    )
    keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton("✅ بله"), KeyboardButton("❌ خیر")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await update.message.reply_text(text, reply_markup=keyboard)
    return CONFIRM

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.message.text.strip()
    if answer not in ["✅ بله", "❌ خیر"]:
        await update.message.reply_text("لطفاً فقط از دکمه‌ها استفاده کنید.")
        return CONFIRM

    if answer == "✅ بله":
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        tracking_code = f"TRK{random.randint(100000, 999999)}"
        student_code = f"STD{random.randint(1000, 9999)}"

        row = [
            context.user_data['name'],
            context.user_data['phone'],
            context.user_data['national_code'],
            context.user_data['field'],
            now,
            tracking_code,
            student_code,
            context.user_data['companions']
        ]
        worksheet.append_row(row)

        await update.message.reply_text("✅ ثبت نام شما با موفقیت انجام شد.\nکد رهگیری شما: " + tracking_code)
    else:
        await update.message.reply_text("❌ ثبت نام لغو شد.")

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ثبت نام لغو شد.")
    return ConversationHandler.END

if __name__ == '__main__':
    TOKEN = os.environ['BOT_TOKEN']  #  Railway

    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, phone)],
            NATIONAL_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, national_code)],
            FIELD: [MessageHandler(filters.TEXT & ~filters.COMMAND, field)],
            COMPANIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, companions)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    app.add_handler(conv_handler)
    print("✅ Running")
    app.run_polling()

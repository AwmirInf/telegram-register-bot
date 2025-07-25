# 1. پایه: از نسخه پایتون رسمی استفاده می‌کنیم
FROM python:3.11-slim

# 2. تعیین پوشه کاری داخل کانتینر
WORKDIR /app

# 3. کپی کردن فایل requirements.txt به کانتینر
COPY requirements.txt .

# 4. نصب کتابخانه‌های مورد نیاز
RUN pip install --no-cache-dir -r requirements.txt

# 5. کپی کل کد برنامه به کانتینر
COPY . .

# 6. دستور شروع اجرای ربات (وقتی کانتینر run می‌شود)
CMD ["python", "bot.py"]

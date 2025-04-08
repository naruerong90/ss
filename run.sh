#!/bin/bash
# สคริปต์สำหรับเริ่มเซิร์ฟเวอร์ Shop Counter

# ตั้งค่า environment variable
export FLASK_APP=main.py
export FLASK_ENV=production

# สร้างโฟลเดอร์ที่จำเป็น
mkdir -p logs
mkdir -p data
mkdir -p uploads
mkdir -p snapshots
mkdir -p exports/reports
mkdir -p backups

# ตรวจสอบว่ามีไฟล์ config.ini หรือไม่
if [ ! -f config.ini ]; then
    echo "ไม่พบไฟล์ config.ini จะสร้างไฟล์ตั้งค่าเริ่มต้น..."
    python main.py
fi

# เริ่มต้นฐานข้อมูล (ถ้ายังไม่มี)
if [ ! -f data/shop_counter.db ]; then
    echo "กำลังเริ่มต้นฐานข้อมูล..."
    python main.py --init-db
fi

# เริ่มเซิร์ฟเวอร์
echo "กำลังเริ่มเซิร์ฟเวอร์ Shop Counter..."
python main.py --host=0.0.0.0 --port=8000
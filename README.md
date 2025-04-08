# Shop Counter Server

ระบบเซิร์ฟเวอร์สำหรับจัดการการนับลูกค้าจากกล้องวงจรปิด

## คุณสมบัติ

- รับและประมวลผลข้อมูลจากกล้องวงจรปิดหลายตัว
- แสดงจำนวนลูกค้าปัจจุบันและสถิติการเข้า-ออกของลูกค้า
- สร้างรายงานและกราฟแสดงผลข้อมูลตามช่วงเวลา
- จัดการอุปกรณ์และกล้องที่เชื่อมต่อกับระบบ
- ระบบบริหารจัดการผู้ใช้และสิทธิ์การเข้าถึง
- API สำหรับเชื่อมต่อกับอุปกรณ์และแอพพลิเคชันอื่นๆ

## ความต้องการของระบบ

- Python 3.9 หรือสูงกว่า
- SQLite (หรือ MySQL, PostgreSQL สำหรับระบบขนาดใหญ่)
- ระบบปฏิบัติการ Linux, Windows หรือ macOS

## การติดตั้ง

1. โคลนหรือดาวน์โหลดโปรเจค

```
git clone https://github.com/your-username/shop-counter-server.git
cd shop-counter-server
```

2. ติดตั้ง dependencies

```
pip install -r requirements.txt
```

3. สร้างไฟล์การตั้งค่าและฐานข้อมูลเริ่มต้น

```
python main.py --init-db
```

4. เปิดไฟล์ `config.ini` และแก้ไขการตั้งค่าตามต้องการ เช่น:
   - ชื่อผู้ใช้และรหัสผ่าน admin
   - API URLs
   - การตั้งค่าฐานข้อมูล (สำหรับระบบขนาดใหญ่)

## การใช้งาน

### เริ่มเซิร์ฟเวอร์

```
./run.sh
```

หรือเริ่มแบบกำหนดค่าเอง:

```
python main.py --host 0.0.0.0 --port 8000
```

### เข้าถึงเว็บแอปพลิเคชัน

เปิดเบราว์เซอร์และเข้าไปที่ `http://localhost:8000`

ล็อกอินโดยใช้:
- ชื่อผู้ใช้: `admin`
- รหัสผ่าน: `ShopCounter@2025` (หรือรหัสที่กำหนดใน config.ini)

## โครงสร้างโปรเจค

```
shop_counter_server/
├── main.py                    # จุดเริ่มต้นเซิร์ฟเวอร์
├── config.ini                 # ไฟล์การตั้งค่า
├── requirements.txt           # รายการ dependencies ที่จำเป็น
├── run.sh                     # สคริปต์เริ่มการทำงาน
│
├── server/                    # โค้ดหลักของเซิร์ฟเวอร์
│   ├── app.py                 # แอปพลิเคชัน Flask
│   ├── config_manager.py      # จัดการการตั้งค่า
│   ├── db.py                  # จัดการฐานข้อมูล
│   └── utils.py               # ฟังก์ชันช่วยเหลือ
│
├── api/                       # ส่วน API
│   ├── v1/                    # API เวอร์ชัน 1
│   │   ├── devices_bp.py      # API จัดการอุปกรณ์
│   │   ├── customer_counts_bp.py # API จัดการข้อมูลการนับลูกค้า
│   │   ├── snapshots_bp.py    # API จัดการภาพ
│   │   └── auth_bp.py         # API การยืนยันตัวตน
│   │
│   └── middleware/            # middleware สำหรับ API
│       └── auth.py            # ตรวจสอบการยืนยันตัวตน
│
├── models/                    # โมเดลข้อมูล
│   ├── user.py                # โมเดลผู้ใช้
│   ├── branch.py              # โมเดลสาขา
│   ├── customer_count.py      # โมเดลข้อมูลการนับลูกค้า
│   ├── snapshot.py            # โมเดลภาพสแนปช็อต
│   └── device.py              # โมเดลอุปกรณ์
│
├── web/                       # หน้าเว็บสำหรับผู้ดูแลระบบ
│   ├── routes.py              # กำหนดเส้นทาง URL
│   ├── templates/             # เทมเพลต
│   └── static/                # ไฟล์ static
│
├── logs/                      # โฟลเดอร์สำหรับไฟล์ล็อก
│   ├── server.log             # ล็อกหลัก
│   └── access.log             # ล็อกการเข้าถึง
│
├── uploads/                   # โฟลเดอร์สำหรับไฟล์ที่อัพโหลด
├── snapshots/                 # โฟลเดอร์สำหรับภาพถ่าย
├── exports/                   # โฟลเดอร์สำหรับส่งออกข้อมูล
└── backups/                   # โฟลเดอร์สำหรับสำรองข้อมูล
```

## API Reference

### การรับรองความถูกต้อง

ส่วน API ต้องการการยืนยันตัวตนด้วย JWT Token ยกเว้น:
- `/api/v1/auth/login`
- `/api/v1/devices/register`
- `/api/v1/devices/heartbeat`
- `/api/v1/devices/check-update`
- `/api/v1/traffic/realtime`
- `/api/v1/traffic/batch`
- `/api/v1/snapshots/cameras/*/snapshot`

### การนับลูกค้า

- `POST /api/v1/traffic/realtime` - บันทึกข้อมูลการนับลูกค้าแบบเรียลไทม์
- `POST /api/v1/traffic/batch` - บันทึกข้อมูลการนับลูกค้าแบบกลุ่ม
- `GET /api/v1/traffic/current` - ดึงข้อมูลจำนวนลูกค้าปัจจุบันของทุกสาขา
- `GET /api/v1/traffic/history/<branch_id>` - ดึงข้อมูลประวัติการนับลูกค้าของสาขา

### ภาพสแนปช็อต

- `POST /api/v1/snapshots/cameras/<camera_id>/snapshot` - อัพโหลดภาพสแนปช็อตจากกล้อง
- `GET /api/v1/snapshots/latest/<branch_id>` - ดึงภาพสแนปช็อตล่าสุดของแต่ละกล้องในสาขา
- `GET /api/v1/snapshots/camera/<camera_id>` - ดึงภาพสแนปช็อตของกล้อง
- `GET /api/v1/snapshots/view/<snapshot_id>` - ดูภาพสแนปช็อต

### อุปกรณ์

- `POST /api/v1/devices/register` - ลงทะเบียนอุปกรณ์ใหม่หรืออัพเดตข้อมูลอุปกรณ์ที่มีอยู่แล้ว
- `POST /api/v1/devices/heartbeat` - บันทึกการเต้นของหัวใจของอุปกรณ์
- `POST /api/v1/devices/check-update` - ตรวจสอบการอัพเดต
- `GET /api/v1/devices` - ดึงข้อมูลอุปกรณ์ทั้งหมด

### การยืนยันตัวตน

- `POST /api/v1/auth/login` - ล็อกอินเข้าสู่ระบบ
- `GET /api/v1/auth/profile` - ดึงข้อมูลโปรไฟล์ผู้ใช้
- `POST /api/v1/auth/change-password` - เปลี่ยนรหัสผ่าน
- `POST /api/v1/auth/forgot-password` - ขอรีเซ็ตรหัสผ่าน
- `POST /api/v1/auth/reset-password` - รีเซ็ตรหัสผ่าน

## การสำรองข้อมูลและการกู้คืน

ระบบจะสร้างไฟล์สำรองข้อมูลอัตโนมัติไว้ในโฟลเดอร์ `backups/` คุณสามารถสร้างไฟล์สำรองข้อมูลด้วยตัวเองได้โดยใช้คำสั่ง:

```
python main.py --backup
```

การกู้คืนจากไฟล์สำรองข้อมูล:

```
python main.py --restore backups/backup_20250407123456.db
```

## การแก้ไขปัญหา

หากเกิดปัญหา คุณสามารถตรวจสอบล็อกได้ที่ `logs/server.log` และ `logs/access.log`

## การพัฒนาต่อ

ระบบนี้สามารถพัฒนาต่อได้ เช่น:
1. เพิ่มการวิเคราะห์ข้อมูลขั้นสูง
2. เพิ่มการรองรับฐานข้อมูลอื่นๆ
3. เพิ่มการแจ้งเตือนเมื่อจำนวนลูกค้าเกินกำหนด
4. ปรับปรุงส่วนติดต่อผู้ใช้ด้วย React หรือ Vue.js

## ลิขสิทธิ์

ซอฟต์แวร์นี้เป็นลิขสิทธิ์ของบริษัทของคุณ
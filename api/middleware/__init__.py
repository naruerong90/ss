# api/middleware/__init__.py - กำหนดให้โฟลเดอร์ middleware เป็น Python package

# นำเข้าโมดูลพื้นฐาน
import logging

# ตั้งค่า logger สำหรับ middleware
logger = logging.getLogger(__name__)

# นำเข้าฟังก์ชันที่จำเป็นจาก middleware ต่างๆ
from api.middleware.auth import token_required, admin_required, generate_token

# สามารถเพิ่มโค้ดอื่นๆ ที่เกี่ยวข้องกับ middleware ได้ที่นี่
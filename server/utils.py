# server/utils.py - ฟังก์ชันช่วยเหลือทั่วไปสำหรับเซิร์ฟเวอร์
import os
import base64
import json
import logging
import hashlib
import secrets
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import pytz

logger = logging.getLogger(__name__)

def generate_timestamp():
    """
    สร้างเวลาปัจจุบันในรูปแบบ ISO 8601
    
    Returns:
        str: เวลาปัจจุบันในรูปแบบ ISO 8601
    """
    return datetime.now().isoformat()

def generate_filename(prefix, extension):
    """
    สร้างชื่อไฟล์ที่ไม่ซ้ำกันโดยใช้เวลาปัจจุบันและค่าสุ่ม
    
    Args:
        prefix: คำนำหน้าของชื่อไฟล์
        extension: นามสกุลไฟล์ (ไม่ต้องมีจุดนำหน้า)
        
    Returns:
        str: ชื่อไฟล์ที่ไม่ซ้ำกัน
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_str = secrets.token_hex(4)
    return f"{prefix}_{timestamp}_{random_str}.{extension}"

def save_base64_image(base64_data, folder, filename=None):
    """
    บันทึกข้อมูลรูปภาพที่อยู่ในรูปแบบ base64
    
    Args:
        base64_data: ข้อมูลรูปภาพในรูปแบบ base64 (อาจมีหรือไม่มี header)
        folder: โฟลเดอร์ที่จะบันทึกไฟล์
        filename: ชื่อไฟล์ที่จะบันทึก (ถ้าไม่ระบุจะสร้างชื่อใหม่)
        
    Returns:
        str: พาธไปยังไฟล์ที่บันทึก
    """
    # ตรวจสอบและสร้างโฟลเดอร์
    os.makedirs(folder, exist_ok=True)
    
    # ลบ header ของ base64 ถ้ามี
    if ',' in base64_data:
        base64_data = base64_data.split(',')[1]
    
    # แปลง base64 เป็นข้อมูลรูปภาพ
    image_data = base64.b64decode(base64_data)
    
    # สร้างชื่อไฟล์ถ้าไม่ได้ระบุ
    if filename is None:
        filename = generate_filename("image", "jpg")
    
    # สร้างพาธเต็ม
    file_path = os.path.join(folder, filename)
    
    # บันทึกไฟล์
    with open(file_path, 'wb') as f:
        f.write(image_data)
    
    logger.info(f"บันทึกรูปภาพไปยัง {file_path} สำเร็จ")
    
    return file_path

def hash_password(password):
    """
    แฮชรหัสผ่านโดยใช้ SHA-256
    
    Args:
        password: รหัสผ่านที่ต้องการแฮช
        
    Returns:
        str: รหัสผ่านที่ผ่านการแฮชแล้ว
    """
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(hashed_password, plain_password):
    """
    ตรวจสอบว่ารหัสผ่านตรงกับรหัสผ่านที่แฮชไว้หรือไม่
    
    Args:
        hashed_password: รหัสผ่านที่ผ่านการแฮชแล้ว
        plain_password: รหัสผ่านที่ต้องการตรวจสอบ
        
    Returns:
        bool: True ถ้ารหัสผ่านตรงกัน, False ถ้าไม่ตรงกัน
    """
    return hashed_password == hash_password(plain_password)

def generate_token():
    """
    สร้างโทเค็นที่ไม่ซ้ำกัน
    
    Returns:
        str: โทเค็นที่ไม่ซ้ำกัน
    """
    return secrets.token_hex(32)

def create_backup(config):
    """
    สร้างไฟล์สำรองข้อมูลของฐานข้อมูล
    
    Args:
        config: อ็อบเจกต์ ConfigParser ที่มีการตั้งค่า
        
    Returns:
        str: พาธไปยังไฟล์สำรองข้อมูล หรือ None ถ้าไม่สามารถสร้างได้
    """
    try:
        # ตรวจสอบประเภทฐานข้อมูล
        db_type = config.get('database', 'type')
        if db_type != 'sqlite':
            logger.error(f"ไม่รองรับการสำรองข้อมูลสำหรับฐานข้อมูลประเภท {db_type}")
            return None
        
        # พาธไปยังไฟล์ฐานข้อมูล
        db_path = os.path.join(
            config.get('database', 'path'),
            config.get('database', 'name')
        )
        
        # ตรวจสอบว่าไฟล์ฐานข้อมูลมีอยู่หรือไม่
        if not os.path.exists(db_path):
            logger.error(f"ไม่พบไฟล์ฐานข้อมูล {db_path}")
            return None
        
        # สร้างโฟลเดอร์สำหรับไฟล์สำรองข้อมูล
        backup_folder = config.get('app', 'backup_folder')
        os.makedirs(backup_folder, exist_ok=True)
        
        # สร้างชื่อไฟล์สำรองข้อมูล
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        backup_filename = f"backup_{timestamp}.db"
        backup_path = os.path.join(backup_folder, backup_filename)
        
        # คัดลอกไฟล์ฐานข้อมูล
        shutil.copy2(db_path, backup_path)
        
        logger.info(f"สร้างไฟล์สำรองข้อมูลไปยัง {backup_path} สำเร็จ")
        
        # ลบไฟล์สำรองข้อมูลเก่า
        cleanup_old_backups(backup_folder, 10)  # เก็บไว้ 10 ไฟล์ล่าสุด
        
        return backup_path
    
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการสร้างไฟล์สำรองข้อมูล: {str(e)}")
        return None

def cleanup_old_backups(backup_folder, keep_count):
    """
    ลบไฟล์สำรองข้อมูลเก่าเกินกว่าจำนวนที่ต้องการเก็บ
    
    Args:
        backup_folder: โฟลเดอร์ที่เก็บไฟล์สำรองข้อมูล
        keep_count: จำนวนไฟล์ล่าสุดที่ต้องการเก็บ
    """
    try:
        # หาไฟล์ทั้งหมดในโฟลเดอร์
        backup_files = [f for f in os.listdir(backup_folder) if f.startswith("backup_") and f.endswith(".db")]
        
        # ถ้ามีไฟล์น้อยกว่าหรือเท่ากับจำนวนที่ต้องการเก็บ ไม่ต้องลบ
        if len(backup_files) <= keep_count:
            return
        
        # เรียงไฟล์ตามเวลาที่สร้าง (เก่าสุดอยู่ข้างหน้า)
        backup_files.sort()
        
        # ลบไฟล์เก่าเกินกว่าจำนวนที่ต้องการเก็บ
        files_to_delete = backup_files[:-keep_count]
        for file_name in files_to_delete:
            file_path = os.path.join(backup_folder, file_name)
            os.remove(file_path)
            logger.info(f"ลบไฟล์สำรองข้อมูลเก่า {file_path}")
    
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการลบไฟล์สำรองข้อมูลเก่า: {str(e)}")

def load_timezone(config):
    """
    โหลด timezone จากการตั้งค่า
    
    Args:
        config: อ็อบเจกต์ ConfigParser ที่มีการตั้งค่า
        
    Returns:
        datetime.tzinfo: timezone object
    """
    try:
        timezone_str = config.get('app', 'timezone')
        return pytz.timezone(timezone_str)
    except Exception as e:
        logger.error(f"ไม่สามารถโหลด timezone {timezone_str}: {str(e)}")
        logger.info("ใช้ timezone UTC แทน")
        return pytz.UTC

def format_datetime(dt, config, format_str=None):
    """
    จัดรูปแบบวันที่และเวลาตามการตั้งค่า
    
    Args:
        dt: วันที่และเวลาที่ต้องการจัดรูปแบบ
        config: อ็อบเจกต์ ConfigParser ที่มีการตั้งค่า
        format_str: รูปแบบที่ต้องการ (ถ้าไม่ระบุจะใช้รูปแบบมาตรฐาน)
        
    Returns:
        str: วันที่และเวลาที่จัดรูปแบบแล้ว
    """
    # โหลด timezone จากการตั้งค่า
    tz = load_timezone(config)
    
    # แปลงเวลาเป็น timezone ที่กำหนด
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt).astimezone(tz)
    else:
        dt = dt.astimezone(tz)
    
    # จัดรูปแบบวันที่และเวลา
    if format_str is None:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    else:
        return dt.strftime(format_str)
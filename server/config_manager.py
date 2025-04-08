# server/config_manager.py - จัดการการตั้งค่า
import os
import logging
import secrets
from configparser import ConfigParser

logger = logging.getLogger(__name__)

def load_config(config_path):
    """
    โหลดการตั้งค่าจากไฟล์
    
    Args:
        config_path: พาธไปยังไฟล์การตั้งค่า
        
    Returns:
        อ็อบเจกต์ ConfigParser ที่มีการตั้งค่า
    """
    config = ConfigParser()
    
    try:
        config.read(config_path, encoding='utf-8')
        logger.info(f"โหลดการตั้งค่าจาก {config_path} สำเร็จ")
    except Exception as e:
        logger.error(f"ไม่สามารถโหลดการตั้งค่าจาก {config_path}: {str(e)}")
        raise
    
    return config

def initialize_config(config_path):
    """
    สร้างไฟล์การตั้งค่าเริ่มต้น
    
    Args:
        config_path: พาธที่จะบันทึกไฟล์การตั้งค่า
    """
    config = ConfigParser()
    
    # ส่วนของเซิร์ฟเวอร์
    config['server'] = {
        'host': '0.0.0.0',
        'port': '8000',
        'debug': 'false',
        'secret_key': secrets.token_hex(16),
        'allowed_origins': '*'
    }
    
    # ส่วนของฐานข้อมูล
    config['database'] = {
        'type': 'sqlite',
        'name': 'shop_counter.db',
        'path': 'data',
        'user': '',
        'password': '',
        'host': '',
        'port': ''
    }
    
    # ส่วนของการยืนยันตัวตน
    config['auth'] = {
        'token_expiration': '86400',
        'admin_username': 'admin',
        'admin_password': 'ShopCounter@2025',
        'reset_token_expiration': '3600'
    }
    
    # ส่วนของแอปพลิเคชัน
    config['app'] = {
        'name': 'Shop Counter',
        'company': 'Your Company',
        'logo_path': 'web/static/images/logo.png',
        'timezone': 'Asia/Bangkok',
        'language': 'th',
        'upload_folder': 'uploads',
        'snapshot_folder': 'snapshots',
        'export_folder': 'exports',
        'backup_folder': 'backups'
    }
    
    # ส่วนของล็อก
    config['logs'] = {
        'level': 'INFO',
        'max_size': '10485760',  # 10 MB
        'backup_count': '5'
    }
    
    # ส่วนของอีเมล
    config['email'] = {
        'enabled': 'false',
        'smtp_server': '',
        'smtp_port': '587',
        'sender': 'noreply@example.com',
        'username': '',
        'password': '',
        'use_tls': 'true'
    }
    
    # ส่วนของการอัพเดต
    config['updates'] = {
        'check_for_updates': 'true',
        'update_url': 'https://example.com/updates',
        'update_interval': '86400'
    }
    
    # ส่วนของการวิเคราะห์
    config['analytics'] = {
        'enabled': 'true',
        'retention_days': '90'
    }
    
    # บันทึกการตั้งค่า
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            config.write(f)
        logger.info(f"สร้างไฟล์การตั้งค่าเริ่มต้นที่ {config_path} สำเร็จ")
    except Exception as e:
        logger.error(f"ไม่สามารถสร้างไฟล์การตั้งค่าที่ {config_path}: {str(e)}")
        raise
    
    return config

def update_config(config, config_path):
    """
    อัพเดตการตั้งค่าและบันทึกลงไฟล์
    
    Args:
        config: อ็อบเจกต์ ConfigParser ที่จะบันทึก
        config_path: พาธไปยังไฟล์การตั้งค่า
    """
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            config.write(f)
        logger.info(f"บันทึกการตั้งค่าไปยัง {config_path} สำเร็จ")
        return True
    except Exception as e:
        logger.error(f"ไม่สามารถบันทึกการตั้งค่าไปยัง {config_path}: {str(e)}")
        return False

def get_database_uri(config):
    """
    สร้าง URI สำหรับเชื่อมต่อฐานข้อมูล
    
    Args:
        config: อ็อบเจกต์ ConfigParser ที่มีการตั้งค่าฐานข้อมูล
        
    Returns:
        URI สำหรับเชื่อมต่อฐานข้อมูล
    """
    db_type = config.get('database', 'type')
    db_name = config.get('database', 'name')
    
    if db_type == 'sqlite':
        db_path = config.get('database', 'path')
        db_file = os.path.join(db_path, db_name)
        return f"sqlite:///{db_file}"
    
    elif db_type == 'mysql':
        db_user = config.get('database', 'user')
        db_pass = config.get('database', 'password')
        db_host = config.get('database', 'host')
        db_port = config.get('database', 'port')
        return f"mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    
    elif db_type == 'postgresql':
        db_user = config.get('database', 'user')
        db_pass = config.get('database', 'password')
        db_host = config.get('database', 'host')
        db_port = config.get('database', 'port')
        return f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    
    else:
        raise ValueError(f"ไม่รองรับประเภทฐานข้อมูล: {db_type}")
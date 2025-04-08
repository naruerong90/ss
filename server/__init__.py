# server/__init__.py - กำหนดให้โฟลเดอร์ server เป็น Python package

import logging

# ตั้งค่า logger สำหรับเซิร์ฟเวอร์
logger = logging.getLogger(__name__)

# Server version
__version__ = '1.0.0'

# นำเข้าโมดูลที่จำเป็น
from server.app import create_app
from server.config_manager import load_config, initialize_config, update_config, get_database_uri
from server.db import init_db, create_tables, get_db, get_session, Base
from server.utils import (
    generate_timestamp, generate_filename, save_base64_image,
    hash_password, verify_password, generate_token,
    create_backup, cleanup_old_backups,
    load_timezone, format_datetime
)

# สามารถเพิ่มโค้ดอื่นๆ ที่เกี่ยวข้องกับเซิร์ฟเวอร์ได้ที่นี่
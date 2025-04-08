# main.py - จุดเริ่มต้นเซิร์ฟเวอร์หลักสำหรับระบบนับจำนวนลูกค้า
import os
import sys
import logging
import argparse
from configparser import ConfigParser
from pathlib import Path

# เพิ่ม path ปัจจุบันเข้าไปใน sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from server.app import create_app
from server.config_manager import load_config, initialize_config
from server.db import init_db, create_tables
from models import create_admin_if_not_exists

# ตั้งค่าการบันทึก log
def setup_logging():
    """ตั้งค่าระบบบันทึก log"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # ตั้งค่า root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "server.log"),
            logging.StreamHandler()
        ]
    )
    
    # ตั้งค่า access logger แยก
    access_logger = logging.getLogger('werkzeug')
    access_handler = logging.FileHandler(log_dir / "access.log")
    access_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    access_logger.addHandler(access_handler)
    
    logging.info("เริ่มต้นการทำงานของเซิร์ฟเวอร์ Shop Counter")

def ensure_directories():
    """สร้างโฟลเดอร์ที่จำเป็นทั้งหมด"""
    dirs = [
        "logs", 
        "data", 
        "uploads", 
        "snapshots", 
        "exports/reports", 
        "backups",
        "migrations/versions"
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        
    logging.info("สร้างโฟลเดอร์ที่จำเป็นเรียบร้อยแล้ว")

def parse_arguments():
    """แยกวิเคราะห์อาร์กิวเมนต์จาก command line"""
    parser = argparse.ArgumentParser(description='Shop Counter Server')
    parser.add_argument('--config', type=str, default='config.ini', help='ไฟล์การตั้งค่า')
    parser.add_argument('--host', type=str, help='Host ที่จะใช้เริ่มเซิร์ฟเวอร์')
    parser.add_argument('--port', type=int, help='Port ที่จะใช้เริ่มเซิร์ฟเวอร์')
    parser.add_argument('--debug', action='store_true', help='เริ่มในโหมด debug')
    parser.add_argument('--init-db', action='store_true', help='สร้างฐานข้อมูลใหม่')
    
    return parser.parse_args()

def main():
    """ฟังก์ชันหลักในการเริ่มต้นเซิร์ฟเวอร์"""
    # แยกวิเคราะห์อาร์กิวเมนต์
    args = parse_arguments()
    
    # ตั้งค่าการบันทึก log
    setup_logging()
    
    # สร้างโฟลเดอร์ที่จำเป็น
    ensure_directories()
    
    # โหลดการตั้งค่า
    if not os.path.exists(args.config):
        logging.info(f"ไม่พบไฟล์การตั้งค่า {args.config} กำลังสร้างไฟล์ตั้งค่าเริ่มต้น...")
        initialize_config(args.config)
    
    config = load_config(args.config)
    
    # แทนที่การตั้งค่าด้วยอาร์กิวเมนต์ (ถ้ามี)
    if args.host:
        config.set('server', 'host', args.host)
    if args.port:
        config.set('server', 'port', str(args.port))
    if args.debug:
        config.set('server', 'debug', 'true')
    
    # สร้างฐานข้อมูล
    if args.init_db:
        logging.info("กำลังเริ่มต้นฐานข้อมูล...")
        init_db(config)
        create_tables(config)
        create_admin_if_not_exists(config)
    
    # สร้างแอปพลิเคชัน
    app = create_app(config)
    
    # เริ่มต้นเซิร์ฟเวอร์
    host = config.get('server', 'host')
    port = config.getint('server', 'port')
    debug = config.getboolean('server', 'debug')
    
    logging.info(f"กำลังเริ่มเซิร์ฟเวอร์ที่ {host}:{port} (debug: {debug})")
    app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    main()
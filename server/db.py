# server/db.py - จัดการฐานข้อมูล
import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from server.config_manager import get_database_uri

logger = logging.getLogger(__name__)

# สร้าง Base class สำหรับโมเดลทั้งหมด
Base = declarative_base()

# Engine และ Session สำหรับใช้งานร่วมกัน
engine = None
SessionLocal = None

def init_db(config):
    """
    เริ่มต้นการเชื่อมต่อฐานข้อมูล
    
    Args:
        config: อ็อบเจกต์ ConfigParser ที่มีการตั้งค่าฐานข้อมูล
    """
    global engine, SessionLocal
    
    # ตรวจสอบและสร้างโฟลเดอร์สำหรับฐานข้อมูล SQLite
    if config.get('database', 'type') == 'sqlite':
        db_path = config.get('database', 'path')
        os.makedirs(db_path, exist_ok=True)
    
    # สร้าง URI สำหรับเชื่อมต่อฐานข้อมูล
    db_uri = get_database_uri(config)
    
    # สร้าง Engine
    engine_options = {"echo": config.getboolean('server', 'debug')}
    engine = create_engine(db_uri, **engine_options)
    
    # สร้าง Session factory
    SessionLocal = scoped_session(
        sessionmaker(autocommit=False, autoflush=False, bind=engine)
    )
    
    logger.info(f"เริ่มต้นการเชื่อมต่อฐานข้อมูล {config.get('database', 'type')} สำเร็จ")
    
    return engine

def create_tables(config):
    """
    สร้างตารางทั้งหมดในฐานข้อมูล
    
    Args:
        config: อ็อบเจกต์ ConfigParser ที่มีการตั้งค่าฐานข้อมูล
    """
    global engine
    
    if engine is None:
        engine = init_db(config)
    
    # นำเข้าโมเดลทั้งหมดเพื่อให้สามารถสร้างตารางได้
    from models.user import User
    from models.branch import Branch
    from models.customer import Customer
    from models.employee import Employee
    from models.appointment import Appointment
    from models.customer_count import CustomerCount
    
    # สร้างตารางทั้งหมด
    Base.metadata.create_all(bind=engine)
    logger.info("สร้างตารางฐานข้อมูลทั้งหมดสำเร็จ")

def get_db():
    """
    สร้าง session สำหรับใช้งานฐานข้อมูล
    
    ใช้ในรูปแบบ context manager:
    ```
    with get_db() as db:
        # ทำอะไรกับฐานข้อมูล
    ```
    
    Returns:
        database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_session():
    """
    สร้าง session สำหรับใช้งานฐานข้อมูลแบบธรรมดา
    
    ต้องปิด session เองเมื่อใช้งานเสร็จ:
    ```
    db = get_session()
    try:
        # ทำอะไรกับฐานข้อมูล
    finally:
        db.close()
    ```
    
    Returns:
        database session
    """
    return SessionLocal()
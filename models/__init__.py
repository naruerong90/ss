# models/__init__.py - สร้างฟังก์ชันที่จำเป็นสำหรับโมเดล
import logging
from server.db import get_session
from server.utils import hash_password
from models.user import User

logger = logging.getLogger(__name__)

from models.user import User
from models.branch import Branch
from models.customer import Customer
from models.employee import Employee
from models.appointment import Appointment
from models.customer_count import CustomerCount
from models.snapshot import Snapshot
from models.device import Device


def create_admin_if_not_exists(config):
    """
    สร้างผู้ใช้ admin ถ้ายังไม่มี
    
    Args:
        config: อ็อบเจกต์ ConfigParser ที่มีการตั้งค่า
    """
    db = get_session()
    
    try:
        # ตรวจสอบว่ามีผู้ใช้ admin หรือยัง
        admin = db.query(User).filter_by(username=config.get('auth', 'admin_username')).first()
        
        if not admin:
            # สร้างผู้ใช้ admin
            admin = User(
                username=config.get('auth', 'admin_username'),
                name='System Administrator',
                email='admin@example.com',
                is_admin=True
            )
            admin.set_password(config.get('auth', 'admin_password'))
            
            db.add(admin)
            db.commit()
            
            logger.info(f"สร้างผู้ใช้ admin '{admin.username}' สำเร็จ")
        
    except Exception as e:
        db.rollback()
        logger.error(f"เกิดข้อผิดพลาดในการสร้างผู้ใช้ admin: {str(e)}")
    
    finally:
        db.close()
# models/device.py - โมเดลอุปกรณ์
import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from server.db import Base

class Device(Base):
    """โมเดลอุปกรณ์"""
    
    __tablename__ = 'devices'
    
    id = Column(Integer, primary_key=True)
    device_id = Column(String(100), unique=True, nullable=False)  # เช่น UUID หรือรหัสเฉพาะ
    camera_id = Column(String(50), nullable=False)
    branch_id = Column(String(50), nullable=False)
    ip_address = Column(String(50))
    registration_date = Column(DateTime, default=datetime.now)
    last_seen = Column(DateTime, default=datetime.now)
    status = Column(String(20), default='active')  # active, inactive, maintenance
    version = Column(String(20), default='1.0.0')
    metadata = Column(Text)  # เก็บข้อมูลเพิ่มเติมในรูปแบบ JSON
    
    def __repr__(self):
        return f"<Device {self.device_id}>"
    
    def to_dict(self):
        """แปลงข้อมูลเป็น dictionary"""
        return {
            'id': self.id,
            'device_id': self.device_id,
            'camera_id': self.camera_id,
            'branch_id': self.branch_id,
            'ip_address': self.ip_address,
            'registration_date': self.registration_date.isoformat(),
            'last_seen': self.last_seen.isoformat(),
            'status': self.status,
            'version': self.version,
            'metadata': json.loads(self.metadata) if self.metadata else {}
        }
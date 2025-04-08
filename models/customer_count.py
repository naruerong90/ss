# models/customer_count.py - โมเดลข้อมูลการนับลูกค้า
import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base

# ใช้ Base จาก SQLAlchemy โดยตรงเพื่อป้องกันปัญหาการอิมพอร์ต
Base = declarative_base()

class CustomerCount(Base):
    """โมเดลข้อมูลการนับลูกค้า"""
    
    __tablename__ = 'customer_counts'
    
    id = Column(Integer, primary_key=True)
    camera_id = Column(String(50), nullable=False)
    branch_id = Column(String(50), nullable=False)
    timestamp = Column(DateTime, default=datetime.now, index=True)
    entry_count = Column(Integer, default=0)  # จำนวนคนเข้าในช่วงเวลานี้
    exit_count = Column(Integer, default=0)   # จำนวนคนออกในช่วงเวลานี้
    current_count = Column(Integer, default=0)  # จำนวนคนปัจจุบันในเวลานั้น
    meta_data = Column(Text)  # เก็บข้อมูลเพิ่มเติมในรูปแบบ JSON
    
    def __repr__(self):
        return f"<CustomerCount {self.camera_id} {self.timestamp}>"
    
    def to_dict(self):
        """แปลงข้อมูลเป็น dictionary"""
        return {
            'id': self.id,
            'camera_id': self.camera_id,
            'branch_id': self.branch_id,
            'timestamp': self.timestamp.isoformat(),
            'entry_count': self.entry_count,
            'exit_count': self.exit_count,
            'current_count': self.current_count,
            'meta_data': json.loads(self.metadata) if self.metadata else {}
        }
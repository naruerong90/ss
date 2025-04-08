# models/snapshot.py - โมเดลภาพสแนปช็อต
import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from server.db import Base

class Snapshot(Base):
    """โมเดลภาพสแนปช็อต"""
    
    __tablename__ = 'snapshots'
    
    id = Column(Integer, primary_key=True)
    camera_id = Column(String(50), nullable=False)
    branch_id = Column(String(50), nullable=False)
    timestamp = Column(DateTime, default=datetime.now, index=True)
    filename = Column(String(255), nullable=False)
    reason = Column(String(50), default='periodic')  # periodic, manual, alert
    current_count = Column(Integer, default=0)  # จำนวนคนในภาพ
    metadata = Column(Text)  # เก็บข้อมูลเพิ่มเติมในรูปแบบ JSON
    
    def __repr__(self):
        return f"<Snapshot {self.camera_id} {self.timestamp}>"
    
    def to_dict(self):
        """แปลงข้อมูลเป็น dictionary"""
        return {
            'id': self.id,
            'camera_id': self.camera_id,
            'branch_id': self.branch_id,
            'timestamp': self.timestamp.isoformat(),
            'filename': self.filename,
            'reason': self.reason,
            'current_count': self.current_count,
            'metadata': json.loads(self.metadata) if self.metadata else {}
        }
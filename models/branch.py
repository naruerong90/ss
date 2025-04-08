# models/branch.py - โมเดลสาขา
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Float
from server.db import Base

class Branch(Base):
    """โมเดลสาขา"""
    
    __tablename__ = 'branches'
    
    id = Column(Integer, primary_key=True)
    branch_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    address = Column(Text)
    province = Column(String(50))
    city = Column(String(50))
    postal_code = Column(String(10))
    phone = Column(String(20))
    email = Column(String(100))
    manager_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    open_time = Column(String(8), default='09:00')  # รูปแบบ HH:MM
    close_time = Column(String(8), default='20:00')  # รูปแบบ HH:MM
    current_customer_count = Column(Integer, default=0)
    last_updated = Column(DateTime)
    capacity = Column(Integer, default=100)  # ความจุของสาขา
    latitude = Column(Float)
    longitude = Column(Float)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<Branch {self.branch_id} {self.name}>"
    
    def to_dict(self):
        """แปลงข้อมูลเป็น dictionary"""
        return {
            'id': self.id,
            'branch_id': self.branch_id,
            'name': self.name,
            'address': self.address,
            'province': self.province,
            'city': self.city,
            'postal_code': self.postal_code,
            'phone': self.phone,
            'email': self.email,
            'manager_name': self.manager_name,
            'is_active': self.is_active,
            'open_time': self.open_time,
            'close_time': self.close_time,
            'current_customer_count': self.current_customer_count,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'capacity': self.capacity,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
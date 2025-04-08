# models/customer.py - โมเดลลูกค้า
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from server.db import Base

class Customer(Base):
    """โมเดลลูกค้า"""
    
    __tablename__ = 'customers'
    
    id = Column(Integer, primary_key=True)
    customer_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    email = Column(String(100))
    phone = Column(String(20))
    address = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    last_visit = Column(DateTime)
    
    # ความสัมพันธ์
    appointments = relationship("Appointment", back_populates="customer")
    
    def __repr__(self):
        return f"<Customer {self.customer_id} {self.name}>"
    
    def to_dict(self):
        """แปลงข้อมูลเป็น dictionary"""
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_visit': self.last_visit.isoformat() if self.last_visit else None
        }
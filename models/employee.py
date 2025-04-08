# models/employee.py - โมเดลพนักงาน
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from server.db import Base

class Employee(Base):
    """โมเดลพนักงาน"""
    
    __tablename__ = 'employees'
    
    id = Column(Integer, primary_key=True)
    employee_id = Column(String(50), unique=True, nullable=False)
    branch_id = Column(String(50), ForeignKey('branches.branch_id'), nullable=False)
    name = Column(String(100), nullable=False)
    position = Column(String(100))
    email = Column(String(100))
    phone = Column(String(20))
    address = Column(Text)
    hire_date = Column(DateTime, default=datetime.now)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # ความสัมพันธ์
    branch = relationship("Branch", back_populates="employees")
    
    def __repr__(self):
        return f"<Employee {self.employee_id} {self.name}>"
    
    def to_dict(self):
        """แปลงข้อมูลเป็น dictionary"""
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'branch_id': self.branch_id,
            'name': self.name,
            'position': self.position,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'hire_date': self.hire_date.isoformat() if self.hire_date else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
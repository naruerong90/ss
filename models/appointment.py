# models/appointment.py - โมเดลการนัดหมาย
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from server.db import Base

class Appointment(Base):
    """โมเดลการนัดหมาย"""
    
    __tablename__ = 'appointments'
    
    id = Column(Integer, primary_key=True)
    appointment_id = Column(String(50), unique=True, nullable=False)
    customer_id = Column(String(50), ForeignKey('customers.customer_id'), nullable=True)
    branch_id = Column(String(50), ForeignKey('branches.branch_id'), nullable=False)
    employee_id = Column(String(50), ForeignKey('employees.employee_id'), nullable=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    appointment_date = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=60)
    status = Column(String(20), default='pending')  # pending, confirmed, completed, cancelled
    is_completed = Column(Boolean, default=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # ความสัมพันธ์
    branch = relationship("Branch", back_populates="appointments")
    customer = relationship("Customer", back_populates="appointments")
    employee = relationship("Employee", backref="appointments")
    
    def __repr__(self):
        return f"<Appointment {self.appointment_id} {self.title}>"
    
    def to_dict(self):
        """แปลงข้อมูลเป็น dictionary"""
        return {
            'id': self.id,
            'appointment_id': self.appointment_id,
            'customer_id': self.customer_id,
            'branch_id': self.branch_id,
            'employee_id': self.employee_id,
            'title': self.title,
            'description': self.description,
            'appointment_date': self.appointment_date.isoformat(),
            'duration_minutes': self.duration_minutes,
            'status': self.status,
            'is_completed': self.is_completed,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
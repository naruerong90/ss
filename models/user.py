# models/user.py - โมเดลผู้ใช้
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from server.db import Base
from server.utils import hash_password

class User(Base):
    """โมเดลผู้ใช้"""
    
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    name = Column(String(100))
    email = Column(String(100), unique=True)
    phone = Column(String(20))
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    reset_token = Column(String(100))
    reset_token_expires = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<User {self.username}>"
    
    def set_password(self, password):
        """ตั้งรหัสผ่าน"""
        self.password_hash = hash_password(password)
    
    def check_password(self, password):
        """ตรวจสอบรหัสผ่าน"""
        from server.utils import verify_password
        return verify_password(self.password_hash, password)
    
    def to_dict(self):
        """แปลงข้อมูลเป็น dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'is_admin': self.is_admin,
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
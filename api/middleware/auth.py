# api/middleware/auth.py - ตรวจสอบการยืนยันตัวตน
import logging
import jwt
from functools import wraps
from flask import request, jsonify, g, current_app
from datetime import datetime, timedelta
from models.user import User
from server.db import get_session

logger = logging.getLogger(__name__)

def token_required(f):
    """
    Decorator สำหรับตรวจสอบโทเค็น JWT
    
    Args:
        f: ฟังก์ชันที่จะตรวจสอบโทเค็น
        
    Returns:
        wrapper: ฟังก์ชันที่ครอบด้วยการตรวจสอบโทเค็น
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = None
        
        # ตรวจสอบโทเค็นจาก header
        auth_header = request.headers.get('Authorization')
        if auth_header:
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({
                'success': False,
                'message': 'ไม่พบโทเค็น กรุณาล็อกอินก่อน'
            }), 401
        
        try:
            # ถอดรหัสโทเค็น
            data = jwt.decode(
                token, 
                current_app.config['SECRET_KEY'],
                algorithms=['HS256']
            )
            
            # ดึงข้อมูลผู้ใช้
            db = get_session()
            user = db.query(User).filter_by(id=data['user_id']).first()
            db.close()
            
            if not user:
                return jsonify({
                    'success': False,
                    'message': 'ไม่พบผู้ใช้'
                }), 401
            
            # เก็บข้อมูลผู้ใช้ใน g object สำหรับใช้ในฟังก์ชันต่อไป
            g.user = user
            
        except jwt.ExpiredSignatureError:
            return jsonify({
                'success': False,
                'message': 'โทเค็นหมดอายุ กรุณาล็อกอินใหม่'
            }), 401
        except jwt.InvalidTokenError:
            return jsonify({
                'success': False,
                'message': 'โทเค็นไม่ถูกต้อง กรุณาล็อกอินใหม่'
            }), 401
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการตรวจสอบโทเค็น: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'เกิดข้อผิดพลาดในการตรวจสอบโทเค็น'
            }), 500
        
        return f(*args, **kwargs)
    
    return wrapper

def admin_required(f):
    """
    Decorator สำหรับตรวจสอบว่าเป็น admin หรือไม่
    
    Args:
        f: ฟังก์ชันที่จะตรวจสอบว่าเป็น admin
        
    Returns:
        wrapper: ฟังก์ชันที่ครอบด้วยการตรวจสอบว่าเป็น admin
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        # ตรวจสอบว่าผ่านการยืนยันตัวตนหรือยัง
        if not hasattr(g, 'user'):
            return jsonify({
                'success': False,
                'message': 'กรุณาล็อกอินก่อน'
            }), 401
        
        # ตรวจสอบว่าเป็น admin หรือไม่
        if not g.user.is_admin:
            return jsonify({
                'success': False,
                'message': 'ต้องมีสิทธิ์ admin เท่านั้น'
            }), 403
        
        return f(*args, **kwargs)
    
    return wrapper

def generate_token(user):
    """
    สร้างโทเค็น JWT
    
    Args:
        user: อ็อบเจกต์ User
        
    Returns:
        str: โทเค็น JWT
    """
    # กำหนดเวลาหมดอายุ
    expiration = datetime.now() + timedelta(seconds=current_app.config.get('TOKEN_EXPIRATION', 86400))
    
    # สร้าง payload
    payload = {
        'user_id': user.id,
        'username': user.username,
        'is_admin': user.is_admin,
        'exp': expiration
    }
    
    # สร้างโทเค็น
    token = jwt.encode(
        payload,
        current_app.config['SECRET_KEY'],
        algorithm='HS256'
    )
    
    return token
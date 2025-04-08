# api/v1/auth_bp.py - API สำหรับการยืนยันตัวตน
import logging
import secrets
from flask import Blueprint, request, jsonify, g, current_app
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from server.db import get_session
from models.user import User
from api.middleware.auth import token_required, generate_token, admin_required

# สร้าง Blueprint
auth_bp = Blueprint('auth', __name__)

logger = logging.getLogger(__name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """ล็อกอินเข้าสู่ระบบ"""
    try:
        data = request.json
        
        # ตรวจสอบข้อมูลที่จำเป็น
        if 'username' not in data or 'password' not in data:
            return jsonify({
                'success': False,
                'message': 'กรุณาระบุชื่อผู้ใช้และรหัสผ่าน'
            }), 400
        
        db = get_session()
        
        try:
            # ดึงข้อมูลผู้ใช้
            user = db.query(User).filter_by(username=data['username']).first()
            
            # ตรวจสอบผู้ใช้และรหัสผ่าน
            if not user or not user.check_password(data['password']):
                return jsonify({
                    'success': False,
                    'message': 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง'
                }), 401
            
            # ตรวจสอบว่าผู้ใช้ยังใช้งานอยู่หรือไม่
            if not user.is_active:
                return jsonify({
                    'success': False,
                    'message': 'บัญชีผู้ใช้นี้ถูกระงับการใช้งาน'
                }), 403
            
            # อัพเดตเวลาเข้าสู่ระบบล่าสุด
            user.last_login = datetime.now()
            db.commit()
            
            # สร้างโทเค็น
            token = generate_token(user)
            
            # ส่งข้อมูลผู้ใช้และโทเค็นกลับไป
            return jsonify({
                'success': True,
                'message': 'เข้าสู่ระบบสำเร็จ',
                'token': token,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'name': user.name,
                    'email': user.email,
                    'is_admin': user.is_admin
                }
            })
        
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"เกิดข้อผิดพลาดในการดึงข้อมูล: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'เกิดข้อผิดพลาดในการดึงข้อมูล'
            }), 500
        
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการเข้าสู่ระบบ: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'เกิดข้อผิดพลาด: ' + str(e)
        }), 500

@auth_bp.route('/profile', methods=['GET'])
@token_required
def get_profile():
    """ดึงข้อมูลโปรไฟล์ผู้ใช้"""
    try:
        # ดึงข้อมูลผู้ใช้จาก g object
        user = g.user
        
        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'name': user.name,
                'email': user.email,
                'phone': user.phone,
                'is_admin': user.is_admin,
                'last_login': user.last_login.isoformat() if user.last_login else None
            }
        })
    
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการดึงข้อมูลโปรไฟล์: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'เกิดข้อผิดพลาด: ' + str(e)
        }), 500

@auth_bp.route('/change-password', methods=['POST'])
@token_required
def change_password():
    """เปลี่ยนรหัสผ่าน"""
    try:
        data = request.json
        
        # ตรวจสอบข้อมูลที่จำเป็น
        if 'current_password' not in data or 'new_password' not in data:
            return jsonify({
                'success': False,
                'message': 'กรุณาระบุรหัสผ่านปัจจุบันและรหัสผ่านใหม่'
            }), 400
        
        # ดึงข้อมูลผู้ใช้จาก g object
        user = g.user
        
        # ตรวจสอบรหัสผ่านปัจจุบัน
        if not user.check_password(data['current_password']):
            return jsonify({
                'success': False,
                'message': 'รหัสผ่านปัจจุบันไม่ถูกต้อง'
            }), 401
        
        # ตรวจสอบรหัสผ่านใหม่
        new_password = data['new_password']
        if len(new_password) < 8:
            return jsonify({
                'success': False,
                'message': 'รหัสผ่านใหม่ต้องมีความยาวอย่างน้อย 8 ตัวอักษร'
            }), 400
        
        db = get_session()
        
        try:
            # อัพเดตรหัสผ่าน
            user.set_password(new_password)
            db.add(user)
            db.commit()
            
            return jsonify({
                'success': True,
                'message': 'เปลี่ยนรหัสผ่านสำเร็จ'
            })
        
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"เกิดข้อผิดพลาดในการอัพเดตข้อมูล: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'เกิดข้อผิดพลาดในการอัพเดตข้อมูล'
            }), 500
        
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการเปลี่ยนรหัสผ่าน: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'เกิดข้อผิดพลาด: ' + str(e)
        }), 500

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """ขอรีเซ็ตรหัสผ่าน"""
    try:
        data = request.json
        
        # ตรวจสอบข้อมูลที่จำเป็น
        if 'username' not in data and 'email' not in data:
            return jsonify({
                'success': False,
                'message': 'กรุณาระบุชื่อผู้ใช้หรืออีเมล'
            }), 400
        
        db = get_session()
        
        try:
            # ดึงข้อมูลผู้ใช้
            user = None
            if 'username' in data:
                user = db.query(User).filter_by(username=data['username']).first()
            elif 'email' in data:
                user = db.query(User).filter_by(email=data['email']).first()
            
            if not user:
                return jsonify({
                    'success': False,
                    'message': 'ไม่พบบัญชีผู้ใช้'
                }), 404
            
            # สร้างโทเค็นสำหรับรีเซ็ตรหัสผ่าน
            reset_token = secrets.token_hex(16)
            reset_token_expires = datetime.now() + timedelta(hours=1)
            
            # บันทึกโทเค็นลงฐานข้อมูล
            user.reset_token = reset_token
            user.reset_token_expires = reset_token_expires
            db.commit()
            
            # ในอนาคตควรส่งอีเมลแจ้งลิงก์รีเซ็ตรหัสผ่าน
            # แต่ในตัวอย่างนี้จะส่งโทเค็นกลับไปเลย
            
            return jsonify({
                'success': True,
                'message': 'กรุณาตรวจสอบอีเมลของคุณเพื่อรีเซ็ตรหัสผ่าน',
                'reset_token': reset_token  # ไม่ควรส่งกลับไปในระบบจริง
            })
        
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"เกิดข้อผิดพลาดในการดึงข้อมูล: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'เกิดข้อผิดพลาดในการดึงข้อมูล'
            }), 500
        
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการขอรีเซ็ตรหัสผ่าน: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'เกิดข้อผิดพลาด: ' + str(e)
        }), 500

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """รีเซ็ตรหัสผ่าน"""
    try:
        data = request.json
        
        # ตรวจสอบข้อมูลที่จำเป็น
        if 'reset_token' not in data or 'new_password' not in data:
            return jsonify({
                'success': False,
                'message': 'กรุณาระบุโทเค็นและรหัสผ่านใหม่'
            }), 400
        
        db = get_session()
        
        try:
            # ดึงข้อมูลผู้ใช้ที่มีโทเค็นตรงกัน
            user = db.query(User).filter_by(reset_token=data['reset_token']).first()
            
            if not user:
                return jsonify({
                    'success': False,
                    'message': 'โทเค็นไม่ถูกต้อง'
                }), 400
            
            # ตรวจสอบว่าโทเค็นหมดอายุหรือยัง
            if not user.reset_token_expires or user.reset_token_expires < datetime.now():
                return jsonify({
                    'success': False,
                    'message': 'โทเค็นหมดอายุแล้ว กรุณาขอรีเซ็ตรหัสผ่านใหม่'
                }), 400
            
            # ตรวจสอบรหัสผ่านใหม่
            new_password = data['new_password']
            if len(new_password) < 8:
                return jsonify({
                    'success': False,
                    'message': 'รหัสผ่านใหม่ต้องมีความยาวอย่างน้อย 8 ตัวอักษร'
                }), 400
            
            # อัพเดตรหัสผ่าน
            user.set_password(new_password)
            user.reset_token = None
            user.reset_token_expires = None
            db.commit()
            
            return jsonify({
                'success': True,
                'message': 'รีเซ็ตรหัสผ่านสำเร็จ กรุณาเข้าสู่ระบบด้วยรหัสผ่านใหม่'
            })
        
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"เกิดข้อผิดพลาดในการอัพเดตข้อมูล: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'เกิดข้อผิดพลาดในการอัพเดตข้อมูล'
            }), 500
        
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการรีเซ็ตรหัสผ่าน: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'เกิดข้อผิดพลาด: ' + str(e)
        }), 500

@auth_bp.route('/users', methods=['GET'])
@token_required
@admin_required
def get_users():
    """ดึงข้อมูลผู้ใช้ทั้งหมด (เฉพาะ admin)"""
    try:
        db = get_session()
        
        try:
            # ดึงข้อมูลผู้ใช้ทั้งหมด
            users = db.query(User).all()
            
            # แปลงข้อมูลเป็น JSON
            users_data = []
            for user in users:
                users_data.append({
                    'id': user.id,
                    'username': user.username,
                    'name': user.name,
                    'email': user.email,
                    'phone': user.phone,
                    'is_admin': user.is_admin,
                    'is_active': user.is_active,
                    'last_login': user.last_login.isoformat() if user.last_login else None,
                    'created_at': user.created_at.isoformat(),
                    'updated_at': user.updated_at.isoformat()
                })
            
            return jsonify({
                'success': True,
                'users': users_data,
                'count': len(users_data)
            })
        
        except SQLAlchemyError as e:
            logger.error(f"เกิดข้อผิดพลาดในการดึงข้อมูล: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'เกิดข้อผิดพลาดในการดึงข้อมูล'
            }), 500
        
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการดึงข้อมูลผู้ใช้: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'เกิดข้อผิดพลาด: ' + str(e)
        }), 500

@auth_bp.route('/users', methods=['POST'])
@token_required
@admin_required
def create_user():
    """สร้างผู้ใช้ใหม่ (เฉพาะ admin)"""
    try:
        data = request.json
        
        # ตรวจสอบข้อมูลที่จำเป็น
        required_fields = ['username', 'password', 'name', 'email']
        if not all(field in data for field in required_fields):
            return jsonify({
                'success': False,
                'message': 'ข้อมูลไม่ครบถ้วน'
            }), 400
        
        # ตรวจสอบรหัสผ่าน
        if len(data['password']) < 8:
            return jsonify({
                'success': False,
                'message': 'รหัสผ่านต้องมีความยาวอย่างน้อย 8 ตัวอักษร'
            }), 400
        
        db = get_session()
        
        try:
            # ตรวจสอบว่ามีชื่อผู้ใช้หรืออีเมลนี้อยู่แล้วหรือไม่
            existing_user = db.query(User).filter(
                (User.username == data['username']) | (User.email == data['email'])
            ).first()
            
            if existing_user:
                return jsonify({
                    'success': False,
                    'message': 'ชื่อผู้ใช้หรืออีเมลนี้มีอยู่แล้ว'
                }), 400
            
            # สร้างผู้ใช้ใหม่
            new_user = User(
                username=data['username'],
                name=data['name'],
                email=data['email'],
                phone=data.get('phone', ''),
                is_admin=data.get('is_admin', False),
                is_active=data.get('is_active', True)
            )
            new_user.set_password(data['password'])
            
            db.add(new_user)
            db.commit()
            
            return jsonify({
                'success': True,
                'message': 'สร้างผู้ใช้สำเร็จ',
                'user_id': new_user.id
            })
        
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"เกิดข้อผิดพลาดในการบันทึกข้อมูล: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'เกิดข้อผิดพลาดในการบันทึกข้อมูล'
            }), 500
        
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการสร้างผู้ใช้: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'เกิดข้อผิดพลาด: ' + str(e)
        }), 500

@auth_bp.route('/users/<int:user_id>', methods=['GET'])
@token_required
@admin_required
def get_user(user_id):
    """ดึงข้อมูลผู้ใช้ (เฉพาะ admin)"""
    try:
        db = get_session()
        
        try:
            # ดึงข้อมูลผู้ใช้
            user = db.query(User).filter_by(id=user_id).first()
            
            if not user:
                return jsonify({
                    'success': False,
                    'message': 'ไม่พบผู้ใช้'
                }), 404
            
            # แปลงข้อมูลเป็น JSON
            user_data = {
                'id': user.id,
                'username': user.username,
                'name': user.name,
                'email': user.email,
                'phone': user.phone,
                'is_admin': user.is_admin,
                'is_active': user.is_active,
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'created_at': user.created_at.isoformat(),
                'updated_at': user.updated_at.isoformat()
            }
            
            return jsonify({
                'success': True,
                'user': user_data
            })
        
        except SQLAlchemyError as e:
            logger.error(f"เกิดข้อผิดพลาดในการดึงข้อมูล: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'เกิดข้อผิดพลาดในการดึงข้อมูล'
            }), 500
        
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการดึงข้อมูลผู้ใช้: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'เกิดข้อผิดพลาด: ' + str(e)
        }), 500

@auth_bp.route('/users/<int:user_id>', methods=['PUT'])
@token_required
@admin_required
def update_user(user_id):
    """อัพเดตข้อมูลผู้ใช้ (เฉพาะ admin)"""
    try:
        data = request.json
        
        db = get_session()
        
        try:
            # ดึงข้อมูลผู้ใช้
            user = db.query(User).filter_by(id=user_id).first()
            
            if not user:
                return jsonify({
                    'success': False,
                    'message': 'ไม่พบผู้ใช้'
                }), 404
            
            # อัพเดตข้อมูลผู้ใช้
            if 'name' in data:
                user.name = data['name']
            if 'email' in data:
                # ตรวจสอบว่ามีอีเมลนี้อยู่แล้วหรือไม่
                existing_user = db.query(User).filter(
                    (User.email == data['email']) & (User.id != user_id)
                ).first()
                
                if existing_user:
                    return jsonify({
                        'success': False,
                        'message': 'อีเมลนี้มีอยู่แล้ว'
                    }), 400
                
                user.email = data['email']
            if 'phone' in data:
                user.phone = data['phone']
            if 'is_admin' in data:
                user.is_admin = data['is_admin']
            if 'is_active' in data:
                user.is_active = data['is_active']
            
            db.commit()
            
            return jsonify({
                'success': True,
                'message': 'อัพเดตข้อมูลผู้ใช้สำเร็จ'
            })
        
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"เกิดข้อผิดพลาดในการอัพเดตข้อมูล: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'เกิดข้อผิดพลาดในการอัพเดตข้อมูล'
            }), 500
        
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการอัพเดตข้อมูลผู้ใช้: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'เกิดข้อผิดพลาด: ' + str(e)
        }), 500

@auth_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@token_required
@admin_required
def admin_reset_password(user_id):
    """รีเซ็ตรหัสผ่านผู้ใช้ (เฉพาะ admin)"""
    try:
        data = request.json
        
        # ตรวจสอบข้อมูลที่จำเป็น
        if 'new_password' not in data:
            return jsonify({
                'success': False,
                'message': 'กรุณาระบุรหัสผ่านใหม่'
            }), 400
        
        # ตรวจสอบรหัสผ่านใหม่
        new_password = data['new_password']
        if len(new_password) < 8:
            return jsonify({
                'success': False,
                'message': 'รหัสผ่านใหม่ต้องมีความยาวอย่างน้อย 8 ตัวอักษร'
            }), 400
        
        db = get_session()
        
        try:
            # ดึงข้อมูลผู้ใช้
            user = db.query(User).filter_by(id=user_id).first()
            
            if not user:
                return jsonify({
                    'success': False,
                    'message': 'ไม่พบผู้ใช้'
                }), 404
            
            # อัพเดตรหัสผ่าน
            user.set_password(new_password)
            
            db.commit()
            
            return jsonify({
                'success': True,
                'message': 'รีเซ็ตรหัสผ่านสำเร็จ'
            })
        
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"เกิดข้อผิดพลาดในการอัพเดตข้อมูล: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'เกิดข้อผิดพลาดในการอัพเดตข้อมูล'
            }), 500
        
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการรีเซ็ตรหัสผ่าน: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'เกิดข้อผิดพลาด: ' + str(e)
        }), 500

@auth_bp.route('/users/<int:user_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_user(user_id):
    """ลบผู้ใช้ (เฉพาะ admin)"""
    try:
        # ตรวจสอบว่าไม่ใช่การลบตัวเอง
        if g.user.id == user_id:
            return jsonify({
                'success': False,
                'message': 'ไม่สามารถลบบัญชีของตัวเองได้'
            }), 400
        
        db = get_session()
        
        try:
            # ดึงข้อมูลผู้ใช้
            user = db.query(User).filter_by(id=user_id).first()
            
            if not user:
                return jsonify({
                    'success': False,
                    'message': 'ไม่พบผู้ใช้'
                }), 404
            
            # ลบผู้ใช้
            db.delete(user)
            db.commit()
            
            return jsonify({
                'success': True,
                'message': 'ลบผู้ใช้สำเร็จ'
            })
        
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"เกิดข้อผิดพลาดในการลบข้อมูล: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'เกิดข้อผิดพลาดในการลบข้อมูล'
            }), 500
        
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการลบผู้ใช้: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'เกิดข้อผิดพลาด: ' + str(e)
        }), 500
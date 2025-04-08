# api/v1/branches_bp.py - API สำหรับจัดการสาขา
import logging
import json
from flask import Blueprint, request, jsonify, g
from functools import wraps
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from server.db import get_session
from models.branch import Branch
from api.middleware.auth import token_required, admin_required

# สร้าง Blueprint
branches_bp = Blueprint('branches', __name__)

logger = logging.getLogger(__name__)

@branches_bp.route('', methods=['GET'])
@token_required
def get_branches():
    """ดึงข้อมูลสาขาทั้งหมด"""
    try:
        db = get_session()
        
        try:
            # ดึงข้อมูลสาขาทั้งหมด
            branches = db.query(Branch).all()
            
            # แปลงข้อมูลเป็น JSON
            branches_data = []
            for branch in branches:
                branches_data.append(branch.to_dict())
            
            return jsonify({
                'success': True,
                'branches': branches_data,
                'count': len(branches_data)
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
        logger.error(f"เกิดข้อผิดพลาดในการดึงข้อมูลสาขา: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'เกิดข้อผิดพลาด: ' + str(e)
        }), 500

@branches_bp.route('/<branch_id>', methods=['GET'])
@token_required
def get_branch(branch_id):
    """ดึงข้อมูลสาขาตาม branch_id"""
    try:
        db = get_session()
        
        try:
            # ดึงข้อมูลสาขา
            branch = db.query(Branch).filter_by(branch_id=branch_id).first()
            
            if not branch:
                return jsonify({
                    'success': False,
                    'message': 'ไม่พบสาขา'
                }), 404
            
            # แปลงข้อมูลเป็น JSON
            branch_data = branch.to_dict()
            
            return jsonify({
                'success': True,
                'branch': branch_data
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
        logger.error(f"เกิดข้อผิดพลาดในการดึงข้อมูลสาขา: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'เกิดข้อผิดพลาด: ' + str(e)
        }), 500

@branches_bp.route('', methods=['POST'])
@token_required
@admin_required
def create_branch():
    """สร้างสาขาใหม่ (เฉพาะ admin)"""
    try:
        data = request.json
        
        # ตรวจสอบข้อมูลที่จำเป็น
        required_fields = ['branch_id', 'name']
        if not all(field in data for field in required_fields):
            return jsonify({
                'success': False,
                'message': 'ข้อมูลไม่ครบถ้วน กรุณาระบุ branch_id และ name'
            }), 400
        
        db = get_session()
        
        try:
            # ตรวจสอบว่ามีสาขานี้อยู่แล้วหรือไม่
            existing_branch = db.query(Branch).filter_by(branch_id=data['branch_id']).first()
            
            if existing_branch:
                return jsonify({
                    'success': False,
                    'message': 'มีสาขานี้อยู่แล้ว'
                }), 400
            
            # สร้างสาขาใหม่
            new_branch = Branch(
                branch_id=data['branch_id'],
                name=data['name'],
                address=data.get('address', ''),
                province=data.get('province', ''),
                city=data.get('city', ''),
                postal_code=data.get('postal_code', ''),
                phone=data.get('phone', ''),
                email=data.get('email', ''),
                manager_name=data.get('manager_name', ''),
                is_active=data.get('is_active', True),
                open_time=data.get('open_time', '09:00'),
                close_time=data.get('close_time', '20:00'),
                capacity=data.get('capacity', 100),
                latitude=data.get('latitude'),
                longitude=data.get('longitude')
            )
            
            db.add(new_branch)
            db.commit()
            
            logger.info(f"สร้างสาขาใหม่ {data['branch_id']} สำเร็จ")
            
            return jsonify({
                'success': True,
                'message': 'สร้างสาขาใหม่สำเร็จ',
                'branch_id': new_branch.branch_id
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
        logger.error(f"เกิดข้อผิดพลาดในการสร้างสาขา: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'เกิดข้อผิดพลาด: ' + str(e)
        }), 500

@branches_bp.route('/<branch_id>', methods=['PUT'])
@token_required
@admin_required
def update_branch(branch_id):
    """อัพเดตข้อมูลสาขา (เฉพาะ admin)"""
    try:
        data = request.json
        
        db = get_session()
        
        try:
            # ดึงข้อมูลสาขา
            branch = db.query(Branch).filter_by(branch_id=branch_id).first()
            
            if not branch:
                return jsonify({
                    'success': False,
                    'message': 'ไม่พบสาขา'
                }), 404
            
            # อัพเดตข้อมูลสาขา
            if 'name' in data:
                branch.name = data['name']
            if 'address' in data:
                branch.address = data['address']
            if 'province' in data:
                branch.province = data['province']
            if 'city' in data:
                branch.city = data['city']
            if 'postal_code' in data:
                branch.postal_code = data['postal_code']
            if 'phone' in data:
                branch.phone = data['phone']
            if 'email' in data:
                branch.email = data['email']
            if 'manager_name' in data:
                branch.manager_name = data['manager_name']
            if 'is_active' in data:
                branch.is_active = data['is_active']
            if 'open_time' in data:
                branch.open_time = data['open_time']
            if 'close_time' in data:
                branch.close_time = data['close_time']
            if 'capacity' in data:
                branch.capacity = data['capacity']
            if 'latitude' in data:
                branch.latitude = data['latitude']
            if 'longitude' in data:
                branch.longitude = data['longitude']
            
            branch.updated_at = datetime.now()
            
            db.commit()
            
            logger.info(f"อัพเดตข้อมูลสาขา {branch_id} สำเร็จ")
            
            return jsonify({
                'success': True,
                'message': 'อัพเดตข้อมูลสาขาสำเร็จ'
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
        logger.error(f"เกิดข้อผิดพลาดในการอัพเดตข้อมูลสาขา: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'เกิดข้อผิดพลาด: ' + str(e)
        }), 500

@branches_bp.route('/<branch_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_branch(branch_id):
    """ลบสาขา (เฉพาะ admin)"""
    try:
        db = get_session()
        
        try:
            # ดึงข้อมูลสาขา
            branch = db.query(Branch).filter_by(branch_id=branch_id).first()
            
            if not branch:
                return jsonify({
                    'success': False,
                    'message': 'ไม่พบสาขา'
                }), 404
            
            # ลบสาขา
            db.delete(branch)
            db.commit()
            
            logger.info(f"ลบสาขา {branch_id} สำเร็จ")
            
            return jsonify({
                'success': True,
                'message': 'ลบสาขาสำเร็จ'
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
        logger.error(f"เกิดข้อผิดพลาดในการลบสาขา: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'เกิดข้อผิดพลาด: ' + str(e)
        }), 500

@branches_bp.route('/<branch_id>/current-count', methods=['GET'])
def get_branch_current_count(branch_id):
    """ดึงข้อมูลจำนวนลูกค้าปัจจุบันของสาขา (ไม่ต้องล็อกอิน)"""
    try:
        db = get_session()
        
        try:
            # ดึงข้อมูลสาขา
            branch = db.query(Branch).filter_by(branch_id=branch_id).first()
            
            if not branch:
                return jsonify({
                    'success': False,
                    'message': 'ไม่พบสาขา'
                }), 404
            
            # ดึงข้อมูลจำนวนลูกค้าปัจจุบัน
            return jsonify({
                'success': True,
                'branch_id': branch.branch_id,
                'name': branch.name,
                'current_count': branch.current_customer_count or 0,
                'capacity': branch.capacity or 100,
                'last_updated': branch.last_updated.isoformat() if branch.last_updated else None
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
        logger.error(f"เกิดข้อผิดพลาดในการดึงข้อมูลจำนวนลูกค้าปัจจุบัน: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'เกิดข้อผิดพลาด: ' + str(e)
        }), 500

@branches_bp.route('/current-counts', methods=['GET'])
def get_all_branches_current_count():
    """ดึงข้อมูลจำนวนลูกค้าปัจจุบันของทุกสาขา (ไม่ต้องล็อกอิน)"""
    try:
        db = get_session()
        
        try:
            # ดึงข้อมูลสาขาทั้งหมด
            branches = db.query(Branch).all()
            
            # สร้างข้อมูลผลลัพธ์
            result = []
            for branch in branches:
                result.append({
                    'branch_id': branch.branch_id,
                    'name': branch.name,
                    'current_count': branch.current_customer_count or 0,
                    'capacity': branch.capacity or 100,
                    'last_updated': branch.last_updated.isoformat() if branch.last_updated else None
                })
            
            return jsonify({
                'success': True,
                'branches': result,
                'count': len(result)
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
        logger.error(f"เกิดข้อผิดพลาดในการดึงข้อมูลจำนวนลูกค้าปัจจุบัน: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'เกิดข้อผิดพลาด: ' + str(e)
        }), 500
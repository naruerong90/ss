# api/v1/devices_bp.py - API สำหรับจัดการอุปกรณ์
import logging
import json
from flask import Blueprint, request, jsonify, g
from functools import wraps
from datetime import datetime
import uuid
from sqlalchemy.exc import SQLAlchemyError
from server.db import get_session
from models.device import Device
from api.middleware.auth import token_required

# สร้าง Blueprint
devices_bp = Blueprint('devices', __name__)

logger = logging.getLogger(__name__)

@devices_bp.route('/register', methods=['POST'])
def register_device():
    """ลงทะเบียนอุปกรณ์ใหม่หรืออัพเดตข้อมูลอุปกรณ์ที่มีอยู่แล้ว"""
    try:
        data = request.json
        
        # ตรวจสอบข้อมูลที่จำเป็น
        required_fields = ['device_id', 'camera_id', 'branch_id']
        if not all(field in data for field in required_fields):
            return jsonify({
                'success': False,
                'message': 'ข้อมูลไม่ครบถ้วน กรุณาระบุ device_id, camera_id, และ branch_id'
            }), 400
        
        db = get_session()
        
        try:
            # ตรวจสอบว่ามีอุปกรณ์นี้อยู่แล้วหรือไม่
            device = db.query(Device).filter_by(device_id=data['device_id']).first()
            
            if device:
                # อัพเดตข้อมูลอุปกรณ์ที่มีอยู่แล้ว
                device.camera_id = data['camera_id']
                device.branch_id = data['branch_id']
                device.ip_address = request.remote_addr
                device.last_seen = datetime.now()
                device.status = data.get('status', 'active')
                device.version = data.get('version', '1.0.0')
                device.meta_data = json.dumps(data.get('metadata', {}))
                
                db.commit()
                
                logger.info(f"อัพเดตข้อมูลอุปกรณ์ {data['device_id']} สำเร็จ")
                
                return jsonify({
                    'success': True,
                    'message': 'อัพเดตข้อมูลอุปกรณ์สำเร็จ',
                    'device_id': device.device_id
                })
            else:
                # สร้างอุปกรณ์ใหม่
                new_device = Device(
                    device_id=data['device_id'],
                    camera_id=data['camera_id'],
                    branch_id=data['branch_id'],
                    ip_address=request.remote_addr,
                    registration_date=datetime.now(),
                    last_seen=datetime.now(),
                    status=data.get('status', 'active'),
                    version=data.get('version', '1.0.0'),
                    meta_data=json.dumps(data.get('metadata', {}))
                )
                
                db.add(new_device)
                db.commit()
                
                logger.info(f"ลงทะเบียนอุปกรณ์ใหม่ {data['device_id']} สำเร็จ")
                
                return jsonify({
                    'success': True,
                    'message': 'ลงทะเบียนอุปกรณ์ใหม่สำเร็จ',
                    'device_id': new_device.device_id
                })
                
            # Similar modifications needed for other functions in this file
            # that reference the metadata field
        
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
        logger.error(f"เกิดข้อผิดพลาดในการลงทะเบียนอุปกรณ์: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'เกิดข้อผิดพลาด: ' + str(e)
        }), 500

@devices_bp.route('/heartbeat', methods=['POST'])
def device_heartbeat():
    """บันทึกการเต้นของหัวใจของอุปกรณ์"""
    try:
        data = request.json
        
        # ตรวจสอบข้อมูลที่จำเป็น
        if 'device_id' not in data:
            return jsonify({
                'success': False,
                'message': 'กรุณาระบุ device_id'
            }), 400
        
        db = get_session()
        
        try:
            # ตรวจสอบว่ามีอุปกรณ์นี้อยู่หรือไม่
            device = db.query(Device).filter_by(device_id=data['device_id']).first()
            
            if not device:
                logger.warning(f"ไม่พบอุปกรณ์ {data['device_id']} ในฐานข้อมูล")
                return jsonify({
                    'success': False,
                    'message': 'ไม่พบอุปกรณ์ในฐานข้อมูล กรุณาลงทะเบียนก่อน',
                    'action': 'register'
                }), 404
            
            # อัพเดตเวลาการเห็นล่าสุด
            device.last_seen = datetime.now()
            device.ip_address = request.remote_addr
            
            # อัพเดตสถานะถ้ามี
            if 'status' in data:
                device.status = data['status']
            
            # อัพเดต metadata ถ้ามี
            if 'metadata' in data:
                device.metadata = json.dumps(data['metadata'])
            
            db.commit()
            
            return jsonify({
                'success': True,
                'message': 'บันทึกการเต้นของหัวใจสำเร็จ',
                'timestamp': datetime.now().isoformat()
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
        logger.error(f"เกิดข้อผิดพลาดในการบันทึกการเต้นของหัวใจ: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'เกิดข้อผิดพลาด: ' + str(e)
        }), 500

@devices_bp.route('/check-update', methods=['POST'])
def check_update():
    """ตรวจสอบการอัพเดต"""
    try:
        data = request.json
        
        # ตรวจสอบข้อมูลที่จำเป็น
        if 'device_id' not in data or 'version' not in data:
            return jsonify({
                'success': False,
                'message': 'กรุณาระบุ device_id และ version'
            }), 400
        
        db = get_session()
        
        try:
            # ตรวจสอบว่ามีอุปกรณ์นี้อยู่หรือไม่
            device = db.query(Device).filter_by(device_id=data['device_id']).first()
            
            if not device:
                logger.warning(f"ไม่พบอุปกรณ์ {data['device_id']} ในฐานข้อมูล")
                return jsonify({
                    'success': False,
                    'message': 'ไม่พบอุปกรณ์ในฐานข้อมูล กรุณาลงทะเบียนก่อน',
                    'action': 'register'
                }), 404
            
            # อัพเดตเวลาการเห็นล่าสุด
            device.last_seen = datetime.now()
            
            # ตรวจสอบเวอร์ชัน
            current_version = data['version']
            latest_version = "1.1.0"  # ในอนาคตควรดึงจากฐานข้อมูลหรือไฟล์
            
            # เปรียบเทียบเวอร์ชัน (เวอร์ชันปัจจุบันน้อยกว่าเวอร์ชันล่าสุด)
            # ในที่นี้ใช้การเปรียบเทียบสตริงอย่างง่าย
            has_update = current_version < latest_version
            
            db.commit()
            
            if has_update:
                return jsonify({
                    'success': True,
                    'has_update': True,
                    'version': latest_version,
                    'update_url': "https://example.com/updates/v1.1.0.zip",
                    'release_notes': "รุ่นนี้ปรับปรุงประสิทธิภาพและแก้ไขข้อบกพร่องหลายอย่าง"
                })
            else:
                return jsonify({
                    'success': True,
                    'has_update': False,
                    'version': current_version
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
        logger.error(f"เกิดข้อผิดพลาดในการตรวจสอบการอัพเดต: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'เกิดข้อผิดพลาด: ' + str(e)
        }), 500

@devices_bp.route('', methods=['GET'])
@token_required
def get_devices():
    """ดึงข้อมูลอุปกรณ์ทั้งหมด (ต้องมีการยืนยันตัวตน)"""
    try:
        db = get_session()
        
        try:
            # ดึงข้อมูลอุปกรณ์ทั้งหมด
            devices = db.query(Device).all()
            
            # แปลงข้อมูลเป็น JSON
            devices_data = []
            for device in devices:
                device_data = {
                    'id': device.id,
                    'device_id': device.device_id,
                    'camera_id': device.camera_id,
                    'branch_id': device.branch_id,
                    'ip_address': device.ip_address,
                    'registration_date': device.registration_date.isoformat(),
                    'last_seen': device.last_seen.isoformat(),
                    'status': device.status,
                    'version': device.version,
                    'metadata': json.loads(device.metadata) if device.metadata else {}
                }
                devices_data.append(device_data)
            
            return jsonify({
                'success': True,
                'devices': devices_data,
                'count': len(devices_data)
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
        logger.error(f"เกิดข้อผิดพลาดในการดึงข้อมูลอุปกรณ์: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'เกิดข้อผิดพลาด: ' + str(e)
        }), 500

@devices_bp.route('/<device_id>', methods=['GET'])
@token_required
def get_device(device_id):
    """ดึงข้อมูลอุปกรณ์ตาม device_id (ต้องมีการยืนยันตัวตน)"""
    try:
        db = get_session()
        
        try:
            # ดึงข้อมูลอุปกรณ์
            device = db.query(Device).filter_by(device_id=device_id).first()
            
            if not device:
                return jsonify({
                    'success': False,
                    'message': 'ไม่พบอุปกรณ์'
                }), 404
            
            # แปลงข้อมูลเป็น JSON
            device_data = {
                'id': device.id,
                'device_id': device.device_id,
                'camera_id': device.camera_id,
                'branch_id': device.branch_id,
                'ip_address': device.ip_address,
                'registration_date': device.registration_date.isoformat(),
                'last_seen': device.last_seen.isoformat(),
                'status': device.status,
                'version': device.version,
                'metadata': json.loads(device.metadata) if device.metadata else {}
            }
            
            return jsonify({
                'success': True,
                'device': device_data
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
        logger.error(f"เกิดข้อผิดพลาดในการดึงข้อมูลอุปกรณ์: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'เกิดข้อผิดพลาด: ' + str(e)
        }), 500

@devices_bp.route('/<device_id>', methods=['DELETE'])
@token_required
def delete_device(device_id):
    """ลบอุปกรณ์ตาม device_id (ต้องมีการยืนยันตัวตน)"""
    try:
        db = get_session()
        
        try:
            # ดึงข้อมูลอุปกรณ์
            device = db.query(Device).filter_by(device_id=device_id).first()
            
            if not device:
                return jsonify({
                    'success': False,
                    'message': 'ไม่พบอุปกรณ์'
                }), 404
            
            # ลบอุปกรณ์
            db.delete(device)
            db.commit()
            
            return jsonify({
                'success': True,
                'message': 'ลบอุปกรณ์สำเร็จ'
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
        logger.error(f"เกิดข้อผิดพลาดในการลบอุปกรณ์: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'เกิดข้อผิดพลาด: ' + str(e)
        }), 500
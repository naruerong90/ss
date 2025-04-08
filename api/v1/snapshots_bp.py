# api/v1/snapshots_bp.py - API สำหรับจัดการภาพสแนปช็อต
import os
import logging
import json
from flask import Blueprint, request, jsonify, g, send_file, current_app
from datetime import datetime, timedelta
from sqlalchemy import and_, desc
from sqlalchemy.exc import SQLAlchemyError
from server.db import get_session
from models.snapshot import Snapshot
from models.branch import Branch
from server.utils import save_base64_image, generate_filename
from api.middleware.auth import token_required

# สร้าง Blueprint
snapshots_bp = Blueprint('snapshots', __name__)

logger = logging.getLogger(__name__)

@snapshots_bp.route('/cameras/<camera_id>/snapshot', methods=['POST'])
def upload_snapshot(camera_id):
    """อัพโหลดภาพสแนปช็อตจากกล้อง"""
    try:
        data = request.json
        
        # ตรวจสอบข้อมูลที่จำเป็น
        required_fields = ['camera_id', 'branch_id', 'timestamp', 'image']
        if not all(field in data for field in required_fields):
            return jsonify({
                'success': False,
                'message': 'ข้อมูลไม่ครบถ้วน'
            }), 400
        
        # ตรวจสอบว่า camera_id ตรงกันหรือไม่
        if data['camera_id'] != camera_id:
            return jsonify({
                'success': False,
                'message': 'camera_id ไม่ตรงกัน'
            }), 400
        
        db = get_session()
        
        try:
            # แปลง timestamp เป็น datetime
            if isinstance(data['timestamp'], str):
                timestamp = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
            else:
                timestamp = datetime.now()
            
            # สร้างชื่อไฟล์
            filename = generate_filename(f"snapshot_{camera_id}", "jpg")
            
            # บันทึกรูปภาพ
            snapshot_folder = current_app.config['SNAPSHOT_FOLDER']
            image_path = save_base64_image(data['image'], snapshot_folder, filename)
            
            # บันทึกข้อมูลลงฐานข้อมูล
            new_snapshot = Snapshot(
                camera_id=camera_id,
                branch_id=data['branch_id'],
                timestamp=timestamp,
                filename=filename,
                reason=data.get('reason', 'periodic'),
                current_count=data.get('current_count', 0),
                metadata=json.dumps(data.get('metadata', {}))
            )
            
            db.add(new_snapshot)
            db.commit()
            
            logger.info(f"บันทึกภาพสแนปช็อตจากกล้อง {camera_id} สำเร็จ: {filename}")
            
            return jsonify({
                'success': True,
                'message': 'บันทึกภาพสแนปช็อตสำเร็จ',
                'snapshot_id': new_snapshot.id,
                'filename': filename
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
        logger.error(f"เกิดข้อผิดพลาดในการอัพโหลดภาพสแนปช็อต: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'เกิดข้อผิดพลาด: ' + str(e)
        }), 500

@snapshots_bp.route('/latest/<branch_id>', methods=['GET'])
@token_required
def get_latest_snapshots(branch_id):
    """ดึงภาพสแนปช็อตล่าสุดของแต่ละกล้องในสาขา (ต้องมีการยืนยันตัวตน)"""
    try:
        limit = request.args.get('limit', 5, type=int)
        
        db = get_session()
        
        try:
            # ตรวจสอบว่ามีสาขานี้อยู่หรือไม่
            branch = db.query(Branch).filter_by(branch_id=branch_id).first()
            if not branch:
                return jsonify({
                    'success': False,
                    'message': 'ไม่พบสาขา'
                }), 404
            
            # ดึงรายการกล้องทั้งหมดในสาขา
            camera_snapshots = db.query(
                    Snapshot.camera_id, 
                    func.max(Snapshot.id).label('latest_id')
                ) \
                .filter_by(branch_id=branch_id) \
                .group_by(Snapshot.camera_id) \
                .all()
            
            # ดึงข้อมูลสแนปช็อตล่าสุดของแต่ละกล้อง
            results = []
            for camera_id, latest_id in camera_snapshots:
                snapshot = db.query(Snapshot).filter_by(id=latest_id).first()
                if snapshot:
                    results.append({
                        'id': snapshot.id,
                        'camera_id': snapshot.camera_id,
                        'branch_id': snapshot.branch_id,
                        'timestamp': snapshot.timestamp.isoformat(),
                        'filename': snapshot.filename,
                        'url': f"/api/v1/snapshots/view/{snapshot.id}",
                        'reason': snapshot.reason,
                        'current_count': snapshot.current_count
                    })
            
            # เรียงตาม timestamp ล่าสุด
            results.sort(key=lambda x: x['timestamp'], reverse=True)
            
            # จำกัดจำนวน
            results = results[:limit]
            
            return jsonify({
                'success': True,
                'branch_id': branch_id,
                'branch_name': branch.name,
                'snapshots': results,
                'count': len(results)
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
        logger.error(f"เกิดข้อผิดพลาดในการดึงภาพสแนปช็อตล่าสุด: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'เกิดข้อผิดพลาด: ' + str(e)
        }), 500

@snapshots_bp.route('/camera/<camera_id>', methods=['GET'])
@token_required
def get_camera_snapshots(camera_id):
    """ดึงภาพสแนปช็อตของกล้อง (ต้องมีการยืนยันตัวตน)"""
    try:
        # ดึงพารามิเตอร์
        limit = request.args.get('limit', 10, type=int)
        offset = request.args.get('offset', 0, type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # แปลงวันที่
        start_datetime = None
        end_datetime = None
        if start_date:
            start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
        if end_date:
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        
        db = get_session()
        
        try:
            # ตรวจสอบเงื่อนไขการค้นหา
            conditions = [Snapshot.camera_id == camera_id]
            
            if start_datetime:
                conditions.append(Snapshot.timestamp >= start_datetime)
            if end_datetime:
                conditions.append(Snapshot.timestamp < end_datetime)
            
            # ดึงจำนวนทั้งหมด
            total_count = db.query(Snapshot) \
                .filter(and_(*conditions)) \
                .count()
            
            # ดึงข้อมูลตามเงื่อนไข
            snapshots = db.query(Snapshot) \
                .filter(and_(*conditions)) \
                .order_by(desc(Snapshot.timestamp)) \
                .limit(limit) \
                .offset(offset) \
                .all()
            
            # แปลงข้อมูลเป็น JSON
            results = []
            for snapshot in snapshots:
                results.append({
                    'id': snapshot.id,
                    'camera_id': snapshot.camera_id,
                    'branch_id': snapshot.branch_id,
                    'timestamp': snapshot.timestamp.isoformat(),
                    'filename': snapshot.filename,
                    'url': f"/api/v1/snapshots/view/{snapshot.id}",
                    'reason': snapshot.reason,
                    'current_count': snapshot.current_count,
                    'metadata': json.loads(snapshot.metadata) if snapshot.metadata else {}
                })
            
            return jsonify({
                'success': True,
                'camera_id': camera_id,
                'snapshots': results,
                'count': len(results),
                'total': total_count,
                'limit': limit,
                'offset': offset
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
        logger.error(f"เกิดข้อผิดพลาดในการดึงภาพสแนปช็อตของกล้อง: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'เกิดข้อผิดพลาด: ' + str(e)
        }), 500

@snapshots_bp.route('/view/<int:snapshot_id>', methods=['GET'])
@token_required
def view_snapshot(snapshot_id):
    """ดูภาพสแนปช็อต (ต้องมีการยืนยันตัวตน)"""
    try:
        db = get_session()
        
        try:
            # ดึงข้อมูลสแนปช็อต
            snapshot = db.query(Snapshot).filter_by(id=snapshot_id).first()
            
            if not snapshot:
                return jsonify({
                    'success': False,
                    'message': 'ไม่พบภาพสแนปช็อต'
                }), 404
            
            # สร้างพาธไปยังไฟล์
            snapshot_folder = current_app.config['SNAPSHOT_FOLDER']
            file_path = os.path.join(snapshot_folder, snapshot.filename)
            
            # ตรวจสอบว่าไฟล์มีอยู่หรือไม่
            if not os.path.exists(file_path):
                return jsonify({
                    'success': False,
                    'message': 'ไม่พบไฟล์ภาพสแนปช็อต'
                }), 404
            
            # ส่งไฟล์
            return send_file(file_path, mimetype='image/jpeg')
        
        except SQLAlchemyError as e:
            logger.error(f"เกิดข้อผิดพลาดในการดึงข้อมูล: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'เกิดข้อผิดพลาดในการดึงข้อมูล'
            }), 500
        
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการดูภาพสแนปช็อต: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'เกิดข้อผิดพลาด: ' + str(e)
        }), 500

@snapshots_bp.route('/<int:snapshot_id>', methods=['DELETE'])
@token_required
def delete_snapshot(snapshot_id):
    """ลบภาพสแนปช็อต (ต้องมีการยืนยันตัวตน)"""
    try:
        db = get_session()
        
        try:
            # ดึงข้อมูลสแนปช็อต
            snapshot = db.query(Snapshot).filter_by(id=snapshot_id).first()
            
            if not snapshot:
                return jsonify({
                    'success': False,
                    'message': 'ไม่พบภาพสแนปช็อต'
                }), 404
            
            # สร้างพาธไปยังไฟล์
            snapshot_folder = current_app.config['SNAPSHOT_FOLDER']
            file_path = os.path.join(snapshot_folder, snapshot.filename)
            
            # ลบไฟล์
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # ลบข้อมูลจากฐานข้อมูล
            db.delete(snapshot)
            db.commit()
            
            logger.info(f"ลบภาพสแนปช็อต {snapshot_id} สำเร็จ")
            
            return jsonify({
                'success': True,
                'message': 'ลบภาพสแนปช็อตสำเร็จ'
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
        logger.error(f"เกิดข้อผิดพลาดในการลบภาพสแนปช็อต: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'เกิดข้อผิดพลาด: ' + str(e)
        }), 500

@snapshots_bp.route('/cleanup', methods=['POST'])
@token_required
def cleanup_snapshots():
    """ลบภาพสแนปช็อตเก่ากว่าจำนวนวันที่กำหนด (ต้องมีการยืนยันตัวตน)"""
    try:
        data = request.json
        
        # ตรวจสอบข้อมูลที่จำเป็น
        if 'days' not in data:
            return jsonify({
                'success': False,
                'message': 'กรุณาระบุจำนวนวัน'
            }), 400
        
        days = int(data['days'])
        if days < 1:
            return jsonify({
                'success': False,
                'message': 'จำนวนวันต้องมากกว่า 0'
            }), 400
        
        # คำนวณวันที่ตัด
        cutoff_date = datetime.now() - timedelta(days=days)
        
        db = get_session()
        
        try:
            # ดึงรายการสแนปช็อตที่จะลบ
            snapshots_to_delete = db.query(Snapshot) \
                .filter(Snapshot.timestamp < cutoff_date) \
                .all()
            
            if not snapshots_to_delete:
                return jsonify({
                    'success': True,
                    'message': 'ไม่มีภาพสแนปช็อตที่ต้องลบ',
                    'count': 0
                })
            
            # ลบไฟล์
            snapshot_folder = current_app.config['SNAPSHOT_FOLDER']
            delete_count = 0
            
            for snapshot in snapshots_to_delete:
                # สร้างพาธไปยังไฟล์
                file_path = os.path.join(snapshot_folder, snapshot.filename)
                
                # ลบไฟล์
                if os.path.exists(file_path):
                    os.remove(file_path)
                
                # ลบข้อมูลจากฐานข้อมูล
                db.delete(snapshot)
                delete_count += 1
            
            db.commit()
            
            logger.info(f"ลบภาพสแนปช็อตเก่ากว่า {days} วันจำนวน {delete_count} รายการสำเร็จ")
            
            return jsonify({
                'success': True,
                'message': f'ลบภาพสแนปช็อตเก่ากว่า {days} วันสำเร็จ',
                'count': delete_count
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
        logger.error(f"เกิดข้อผิดพลาดในการลบภาพสแนปช็อตเก่า: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'เกิดข้อผิดพลาด: ' + str(e)
        }), 500
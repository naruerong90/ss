# api/v1/customer_counts_bp.py - API สำหรับจัดการข้อมูลการนับลูกค้า
import logging
import json
from flask import Blueprint, request, jsonify, g
from datetime import datetime, timedelta
from sqlalchemy import func, and_, desc
from sqlalchemy.exc import SQLAlchemyError
from server.db import get_session
from models.customer_count import CustomerCount
from models.branch import Branch
from api.middleware.auth import token_required

# สร้าง Blueprint
customer_counts_bp = Blueprint('customer_counts', __name__)

logger = logging.getLogger(__name__)

@customer_counts_bp.route('/realtime', methods=['POST'])
def record_realtime():
    """บันทึกข้อมูลการนับลูกค้าแบบเรียลไทม์"""
    try:
        data = request.json
        
        # ตรวจสอบข้อมูลที่จำเป็น
        required_fields = ['camera_id', 'branch_id', 'timestamp', 'entry_count', 'exit_count', 'current_count']
        if not all(field in data for field in required_fields):
            return jsonify({
                'success': False,
                'message': 'ข้อมูลไม่ครบถ้วน'
            }), 400
        
        db = get_session()
        
        try:
            # แปลง timestamp เป็น datetime
            if isinstance(data['timestamp'], str):
                timestamp = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
            else:
                timestamp = datetime.now()
            
            # สร้างข้อมูลการนับลูกค้า
            new_count = CustomerCount(
                camera_id=data['camera_id'],
                branch_id=data['branch_id'],
                timestamp=timestamp,
                entry_count=data['entry_count'],
                exit_count=data['exit_count'],
                current_count=data['current_count'],
                metadata=json.dumps(data.get('metadata', {}))
            )
            
            db.add(new_count)
            
            # อัพเดตจำนวนลูกค้าปัจจุบันของสาขา
            branch = db.query(Branch).filter_by(branch_id=data['branch_id']).first()
            if branch:
                branch.current_customer_count = data['current_count']
                branch.last_updated = timestamp
            
            db.commit()
            
            logger.info(f"บันทึกข้อมูลการนับลูกค้าสำหรับกล้อง {data['camera_id']} สำเร็จ")
            
            return jsonify({
                'success': True,
                'message': 'บันทึกข้อมูลสำเร็จ',
                'id': new_count.id
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
        logger.error(f"เกิดข้อผิดพลาดในการบันทึกข้อมูลการนับลูกค้า: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'เกิดข้อผิดพลาด: ' + str(e)
        }), 500

@customer_counts_bp.route('/batch', methods=['POST'])
def record_batch():
    """บันทึกข้อมูลการนับลูกค้าแบบกลุ่ม"""
    try:
        data = request.json
        
        # ตรวจสอบข้อมูลที่จำเป็น
        if 'data' not in data or not isinstance(data['data'], list):
            return jsonify({
                'success': False,
                'message': 'ข้อมูลไม่ถูกต้อง กรุณาส่งข้อมูลในรูปแบบอาร์เรย์'
            }), 400
        
        if len(data['data']) == 0:
            return jsonify({
                'success': True,
                'message': 'ไม่มีข้อมูลที่ต้องบันทึก',
                'count': 0
            })
        
        db = get_session()
        
        try:
            # สร้างข้อมูลการนับลูกค้าทั้งหมด
            count_records = []
            for item in data['data']:
                # ตรวจสอบข้อมูลที่จำเป็น
                required_fields = ['camera_id', 'branch_id', 'timestamp', 'entry_count', 'exit_count', 'current_count']
                if not all(field in item for field in required_fields):
                    continue
                
                # แปลง timestamp เป็น datetime
                if isinstance(item['timestamp'], str):
                    timestamp = datetime.fromisoformat(item['timestamp'].replace('Z', '+00:00'))
                else:
                    timestamp = datetime.now()
                
                # สร้างข้อมูลการนับลูกค้า
                count_record = CustomerCount(
                    camera_id=item['camera_id'],
                    branch_id=item['branch_id'],
                    timestamp=timestamp,
                    entry_count=item['entry_count'],
                    exit_count=item['exit_count'],
                    current_count=item['current_count'],
                    metadata=json.dumps(item.get('metadata', {}))
                )
                
                count_records.append(count_record)
            
            # บันทึกข้อมูลทั้งหมด
            db.add_all(count_records)
            
            # อัพเดตจำนวนลูกค้าปัจจุบันของสาขา
            if count_records:
                # ใช้ข้อมูลล่าสุด
                latest_record = max(count_records, key=lambda r: r.timestamp)
                branch = db.query(Branch).filter_by(branch_id=latest_record.branch_id).first()
                if branch:
                    branch.current_customer_count = latest_record.current_count
                    branch.last_updated = latest_record.timestamp
            
            db.commit()
            
            logger.info(f"บันทึกข้อมูลการนับลูกค้าแบบกลุ่มจำนวน {len(count_records)} รายการสำเร็จ")
            
            return jsonify({
                'success': True,
                'message': 'บันทึกข้อมูลสำเร็จ',
                'count': len(count_records)
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
        logger.error(f"เกิดข้อผิดพลาดในการบันทึกข้อมูลการนับลูกค้าแบบกลุ่ม: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'เกิดข้อผิดพลาด: ' + str(e)
        }), 500

@customer_counts_bp.route('/current', methods=['GET'])
@token_required
def get_current_counts():
    """ดึงข้อมูลจำนวนลูกค้าปัจจุบันของทุกสาขา (ต้องมีการยืนยันตัวตน)"""
    try:
        db = get_session()
        
        try:
            # ดึงข้อมูลสาขาทั้งหมด
            branches = db.query(Branch).all()
            
            results = []
            for branch in branches:
                # ดึงข้อมูลการนับลูกค้าล่าสุดของแต่ละกล้องในสาขา
                cameras = db.query(CustomerCount.camera_id, func.max(CustomerCount.id).label('latest_id')) \
                    .filter_by(branch_id=branch.branch_id) \
                    .group_by(CustomerCount.camera_id) \
                    .all()
                
                camera_counts = []
                total_current_count = 0
                
                for camera_id, latest_id in cameras:
                    latest_count = db.query(CustomerCount).filter_by(id=latest_id).first()
                    if latest_count:
                        camera_counts.append({
                            'camera_id': camera_id,
                            'current_count': latest_count.current_count,
                            'timestamp': latest_count.timestamp.isoformat()
                        })
                        total_current_count += latest_count.current_count
                
                results.append({
                    'branch_id': branch.branch_id,
                    'branch_name': branch.name,
                    'current_count': total_current_count,
                    'cameras': camera_counts,
                    'last_updated': branch.last_updated.isoformat() if branch.last_updated else None
                })
            
            return jsonify({
                'success': True,
                'data': results
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

@customer_counts_bp.route('/history/<branch_id>', methods=['GET'])
@token_required
def get_history(branch_id):
    """ดึงข้อมูลประวัติการนับลูกค้าของสาขา (ต้องมีการยืนยันตัวตน)"""
    try:
        # ดึงพารามิเตอร์
        start_date = request.args.get('start_date', (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'))
        end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
        interval = request.args.get('interval', 'hour')  # hour, day, week, month
        
        # แปลงวันที่
        start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        
        db = get_session()
        
        try:
            # ตรวจสอบว่ามีสาขานี้อยู่หรือไม่
            branch = db.query(Branch).filter_by(branch_id=branch_id).first()
            if not branch:
                return jsonify({
                    'success': False,
                    'message': 'ไม่พบสาขา'
                }), 404
            
            # ดึงข้อมูลตามช่วงเวลา
            # สร้าง SQL ที่เหมาะสมตาม interval ที่ต้องการ
            if interval == 'hour':
                # กรณีรายชั่วโมง
                # ดึงข้อมูลทุกบันทึก แล้วจัดกลุ่มตามชั่วโมงในแอพลิเคชัน
                counts = db.query(CustomerCount) \
                    .filter(and_(
                        CustomerCount.branch_id == branch_id,
                        CustomerCount.timestamp >= start_datetime,
                        CustomerCount.timestamp < end_datetime
                    )) \
                    .order_by(CustomerCount.timestamp) \
                    .all()
                
                # จัดกลุ่มข้อมูลตามชั่วโมง
                hourly_data = {}
                for count in counts:
                    hour_key = count.timestamp.strftime('%Y-%m-%d %H:00:00')
                    if hour_key not in hourly_data:
                        hourly_data[hour_key] = {
                            'timestamp': hour_key,
                            'entry_count': 0,
                            'exit_count': 0,
                            'max_count': 0
                        }
                    
                    hourly_data[hour_key]['entry_count'] += count.entry_count
                    hourly_data[hour_key]['exit_count'] += count.exit_count
                    hourly_data[hour_key]['max_count'] = max(hourly_data[hour_key]['max_count'], count.current_count)
                
                result = list(hourly_data.values())
            
            elif interval == 'day':
                # กรณีรายวัน
                daily_data = {}
                
                counts = db.query(CustomerCount) \
                    .filter(and_(
                        CustomerCount.branch_id == branch_id,
                        CustomerCount.timestamp >= start_datetime,
                        CustomerCount.timestamp < end_datetime
                    )) \
                    .order_by(CustomerCount.timestamp) \
                    .all()
                
                for count in counts:
                    day_key = count.timestamp.strftime('%Y-%m-%d')
                    if day_key not in daily_data:
                        daily_data[day_key] = {
                            'timestamp': day_key,
                            'entry_count': 0,
                            'exit_count': 0,
                            'max_count': 0
                        }
                    
                    daily_data[day_key]['entry_count'] += count.entry_count
                    daily_data[day_key]['exit_count'] += count.exit_count
                    daily_data[day_key]['max_count'] = max(daily_data[day_key]['max_count'], count.current_count)
                
                result = list(daily_data.values())
                
            else:
                # กรณีรายสัปดาห์หรือรายเดือน (จัดการคล้ายกับรายวัน แต่แบ่งกลุ่มตาม week หรือ month)
                # ในที่นี้ไม่ได้เขียนรายละเอียดทั้งหมด
                result = []
            
            return jsonify({
                'success': True,
                'branch_id': branch_id,
                'branch_name': branch.name,
                'interval': interval,
                'start_date': start_date,
                'end_date': end_date,
                'data': result
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
        logger.error(f"เกิดข้อผิดพลาดในการดึงข้อมูลประวัติการนับลูกค้า: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'เกิดข้อผิดพลาด: ' + str(e)
        }), 500

@customer_counts_bp.route('/summary/<branch_id>', methods=['GET'])
@token_required
def get_summary(branch_id):
    """ดึงข้อมูลสรุปการนับลูกค้าของสาขา (ต้องมีการยืนยันตัวตน)"""
    try:
        # ดึงพารามิเตอร์
        start_date = request.args.get('start_date', (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'))
        end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
        
        # แปลงวันที่
        start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        
        db = get_session()
        
        try:
            # ตรวจสอบว่ามีสาขานี้อยู่หรือไม่
            branch = db.query(Branch).filter_by(branch_id=branch_id).first()
            if not branch:
                return jsonify({
                    'success': False,
                    'message': 'ไม่พบสาขา'
                }), 404
            
            # ดึงข้อมูลสรุป
            # รวมจำนวนลูกค้าเข้า
            total_entries = db.query(func.sum(CustomerCount.entry_count)) \
                .filter(and_(
                    CustomerCount.branch_id == branch_id,
                    CustomerCount.timestamp >= start_datetime,
                    CustomerCount.timestamp < end_datetime
                )) \
                .scalar() or 0
            
            # รวมจำนวนลูกค้าออก
            total_exits = db.query(func.sum(CustomerCount.exit_count)) \
                .filter(and_(
                    CustomerCount.branch_id == branch_id,
                    CustomerCount.timestamp >= start_datetime,
                    CustomerCount.timestamp < end_datetime
                )) \
                .scalar() or 0
            
            # จำนวนลูกค้าสูงสุด
            max_count = db.query(func.max(CustomerCount.current_count)) \
                .filter(and_(
                    CustomerCount.branch_id == branch_id,
                    CustomerCount.timestamp >= start_datetime,
                    CustomerCount.timestamp < end_datetime
                )) \
                .scalar() or 0
            
            # หาชั่วโมงที่มีลูกค้าเข้ามากที่สุด
            # ในที่นี้ใช้การจัดกลุ่มตามชั่วโมงแบบง่ายๆ
            busy_hours_data = db.query(
                    func.date_format(CustomerCount.timestamp, '%H:00').label('hour'),
                    func.sum(CustomerCount.entry_count).label('entries')
                ) \
                .filter(and_(
                    CustomerCount.branch_id == branch_id,
                    CustomerCount.timestamp >= start_datetime,
                    CustomerCount.timestamp < end_datetime
                )) \
                .group_by('hour') \
                .order_by(desc('entries')) \
                .limit(5) \
                .all()
            
            busy_hours = [{'hour': hour, 'entries': entries} for hour, entries in busy_hours_data]
            
            # จำนวนลูกค้าเฉลี่ยต่อวัน
            days = (end_datetime - start_datetime).days
            avg_daily_entries = total_entries / max(1, days)
            
            return jsonify({
                'success': True,
                'branch_id': branch_id,
                'branch_name': branch.name,
                'period': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'days': days
                },
                'summary': {
                    'total_entries': total_entries,
                    'total_exits': total_exits,
                    'max_count': max_count,
                    'avg_daily_entries': round(avg_daily_entries, 2),
                    'busy_hours': busy_hours
                }
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
        logger.error(f"เกิดข้อผิดพลาดในการดึงข้อมูลสรุปการนับลูกค้า: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'เกิดข้อผิดพลาด: ' + str(e)
        }), 500

@customer_counts_bp.route('/compare/<branch_id>', methods=['GET'])
@token_required
def compare_periods(branch_id):
    """เปรียบเทียบข้อมูลการนับลูกค้าระหว่างสองช่วงเวลา (ต้องมีการยืนยันตัวตน)"""
    try:
        # ดึงพารามิเตอร์
        period1_start = request.args.get('period1_start', (datetime.now() - timedelta(days=14)).strftime('%Y-%m-%d'))
        period1_end = request.args.get('period1_end', (datetime.now() - timedelta(days=8)).strftime('%Y-%m-%d'))
        period2_start = request.args.get('period2_start', (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'))
        period2_end = request.args.get('period2_end', datetime.now().strftime('%Y-%m-%d'))
        
        # แปลงวันที่
        period1_start_dt = datetime.strptime(period1_start, '%Y-%m-%d')
        period1_end_dt = datetime.strptime(period1_end, '%Y-%m-%d') + timedelta(days=1)
        period2_start_dt = datetime.strptime(period2_start, '%Y-%m-%d')
        period2_end_dt = datetime.strptime(period2_end, '%Y-%m-%d') + timedelta(days=1)
        
        db = get_session()
        
        try:
            # ตรวจสอบว่ามีสาขานี้อยู่หรือไม่
            branch = db.query(Branch).filter_by(branch_id=branch_id).first()
            if not branch:
                return jsonify({
                    'success': False,
                    'message': 'ไม่พบสาขา'
                }), 404
            
            # ดึงข้อมูลช่วงที่ 1
            period1_entries = db.query(func.sum(CustomerCount.entry_count)) \
                .filter(and_(
                    CustomerCount.branch_id == branch_id,
                    CustomerCount.timestamp >= period1_start_dt,
                    CustomerCount.timestamp < period1_end_dt
                )) \
                .scalar() or 0
            
            period1_exits = db.query(func.sum(CustomerCount.exit_count)) \
                .filter(and_(
                    CustomerCount.branch_id == branch_id,
                    CustomerCount.timestamp >= period1_start_dt,
                    CustomerCount.timestamp < period1_end_dt
                )) \
                .scalar() or 0
            
            period1_max = db.query(func.max(CustomerCount.current_count)) \
                .filter(and_(
                    CustomerCount.branch_id == branch_id,
                    CustomerCount.timestamp >= period1_start_dt,
                    CustomerCount.timestamp < period1_end_dt
                )) \
                .scalar() or 0
            
            # ดึงข้อมูลช่วงที่ 2
            period2_entries = db.query(func.sum(CustomerCount.entry_count)) \
                .filter(and_(
                    CustomerCount.branch_id == branch_id,
                    CustomerCount.timestamp >= period2_start_dt,
                    CustomerCount.timestamp < period2_end_dt
                )) \
                .scalar() or 0
            
            period2_exits = db.query(func.sum(CustomerCount.exit_count)) \
                .filter(and_(
                    CustomerCount.branch_id == branch_id,
                    CustomerCount.timestamp >= period2_start_dt,
                    CustomerCount.timestamp < period2_end_dt
                )) \
                .scalar() or 0
            
            period2_max = db.query(func.max(CustomerCount.current_count)) \
                .filter(and_(
                    CustomerCount.branch_id == branch_id,
                    CustomerCount.timestamp >= period2_start_dt,
                    CustomerCount.timestamp < period2_end_dt
                )) \
                .scalar() or 0
            
            # คำนวณความเปลี่ยนแปลง
            entries_change = ((period2_entries - period1_entries) / max(1, period1_entries)) * 100
            exits_change = ((period2_exits - period1_exits) / max(1, period1_exits)) * 100
            max_change = ((period2_max - period1_max) / max(1, period1_max)) * 100
            
            return jsonify({
                'success': True,
                'branch_id': branch_id,
                'branch_name': branch.name,
                'period1': {
                    'start_date': period1_start,
                    'end_date': period1_end,
                    'entries': period1_entries,
                    'exits': period1_exits,
                    'max_count': period1_max
                },
                'period2': {
                    'start_date': period2_start,
                    'end_date': period2_end,
                    'entries': period2_entries,
                    'exits': period2_exits,
                    'max_count': period2_max
                },
                'changes': {
                    'entries': round(entries_change, 2),
                    'exits': round(exits_change, 2),
                    'max_count': round(max_change, 2)
                }
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
        logger.error(f"เกิดข้อผิดพลาดในการเปรียบเทียบข้อมูลการนับลูกค้า: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'เกิดข้อผิดพลาด: ' + str(e)
        }), 500
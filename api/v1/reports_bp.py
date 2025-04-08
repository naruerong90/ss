# api/v1/reports_bp.py - API สำหรับการสร้างรายงาน
import logging
import json
import csv
import io
import os
from flask import Blueprint, request, jsonify, g, current_app, send_file
from functools import wraps
from datetime import datetime, timedelta
from sqlalchemy import func, and_, desc
from sqlalchemy.exc import SQLAlchemyError
from server.db import get_session
from models.customer_count import CustomerCount
from models.branch import Branch
from api.middleware.auth import token_required

# สร้าง Blueprint
reports_bp = Blueprint('reports', __name__)

logger = logging.getLogger(__name__)

@reports_bp.route('/daily/<branch_id>', methods=['GET'])
@token_required
def daily_report(branch_id):
    """สร้างรายงานประจำวันของสาขา"""
    try:
        # ดึงพารามิเตอร์
        date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        output_format = request.args.get('format', 'json')  # json, csv
        
        # แปลงวันที่
        try:
            report_date = datetime.strptime(date_str, '%Y-%m-%d')
            start_date = report_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=1)
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'รูปแบบวันที่ไม่ถูกต้อง (ควรเป็น YYYY-MM-DD)'
            }), 400
        
        db = get_session()
        
        try:
            # ตรวจสอบว่ามีสาขานี้อยู่หรือไม่
            branch = db.query(Branch).filter_by(branch_id=branch_id).first()
            if not branch:
                return jsonify({
                    'success': False,
                    'message': 'ไม่พบสาขา'
                }), 404
            
            # ดึงข้อมูลการนับลูกค้าตามชั่วโมง
            hourly_counts = db.query(
                    func.hour(CustomerCount.timestamp).label('hour'),
                    func.sum(CustomerCount.entry_count).label('entries'),
                    func.sum(CustomerCount.exit_count).label('exits'),
                    func.max(CustomerCount.current_count).label('max_count')
                ) \
                .filter(and_(
                    CustomerCount.branch_id == branch_id,
                    CustomerCount.timestamp >= start_date,
                    CustomerCount.timestamp < end_date
                )) \
                .group_by('hour') \
                .order_by('hour') \
                .all()
            
            # สร้างข้อมูลรายงาน
            hourly_data = []
            total_entries = 0
            total_exits = 0
            max_hour_count = 0
            max_hour = None
            
            for hour, entries, exits, max_count in hourly_counts:
                hourly_data.append({
                    'hour': hour,
                    'time': f"{hour:02d}:00",
                    'entries': entries,
                    'exits': exits,
                    'max_count': max_count
                })
                
                total_entries += entries
                total_exits += exits
                
                if entries > max_hour_count:
                    max_hour_count = entries
                    max_hour = hour
            
            # สร้างข้อมูลสรุป
            summary = {
                'date': date_str,
                'branch_id': branch_id,
                'branch_name': branch.name,
                'total_entries': total_entries,
                'total_exits': total_exits,
                'max_concurrent': max(c[3] for c in hourly_counts) if hourly_counts else 0,
                'busiest_hour': f"{max_hour:02d}:00" if max_hour is not None else None,
                'busiest_hour_count': max_hour_count
            }
            
            # ส่งข้อมูลในรูปแบบที่ต้องการ
            if output_format == 'csv':
                # สร้างไฟล์ CSV
                csv_data = io.StringIO()
                csv_writer = csv.writer(csv_data)
                
                # เขียนส่วนหัว
                csv_writer.writerow(['รายงานประจำวัน', date_str])
                csv_writer.writerow(['สาขา', branch.branch_id, branch.name])
                csv_writer.writerow([])
                csv_writer.writerow(['ชั่วโมง', 'จำนวนลูกค้าเข้า', 'จำนวนลูกค้าออก', 'จำนวนลูกค้าสูงสุด'])
                
                # เขียนข้อมูลรายชั่วโมง
                for hour_data in hourly_data:
                    csv_writer.writerow([
                        hour_data['time'],
                        hour_data['entries'],
                        hour_data['exits'],
                        hour_data['max_count']
                    ])
                
                # เขียนสรุป
                csv_writer.writerow([])
                csv_writer.writerow(['สรุป'])
                csv_writer.writerow(['จำนวนลูกค้าเข้าทั้งหมด', summary['total_entries']])
                csv_writer.writerow(['จำนวนลูกค้าออกทั้งหมด', summary['total_exits']])
                csv_writer.writerow(['จำนวนลูกค้าสูงสุด', summary['max_concurrent']])
                csv_writer.writerow(['ช่วงเวลาที่มีลูกค้าเข้ามากที่สุด', summary['busiest_hour']])
                csv_writer.writerow(['จำนวนลูกค้าในช่วงเวลาที่มากที่สุด', summary['busiest_hour_count']])
                
                # สร้างไฟล์
                csv_data.seek(0)
                
                # สร้างชื่อไฟล์
                filename = f"daily_report_{branch_id}_{date_str}.csv"
                
                # ส่งไฟล์
                return send_file(
                    io.BytesIO(csv_data.getvalue().encode()),
                    mimetype='text/csv',
                    as_attachment=True,
                    download_name=filename
                )
            else:
                # ส่งข้อมูลในรูปแบบ JSON
                return jsonify({
                    'success': True,
                    'report': {
                        'summary': summary,
                        'hourly_data': hourly_data
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
        logger.error(f"เกิดข้อผิดพลาดในการสร้างรายงานประจำวัน: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'เกิดข้อผิดพลาด: ' + str(e)
        }), 500

@reports_bp.route('/weekly/<branch_id>', methods=['GET'])
@token_required
def weekly_report(branch_id):
    """สร้างรายงานประจำสัปดาห์ของสาขา"""
    try:
        # ดึงพารามิเตอร์
        date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        output_format = request.args.get('format', 'json')  # json, csv
        
        # แปลงวันที่
        try:
            report_date = datetime.strptime(date_str, '%Y-%m-%d')
            # หาวันแรกของสัปดาห์ (จันทร์)
            start_date = report_date - timedelta(days=report_date.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=7)
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'รูปแบบวันที่ไม่ถูกต้อง (ควรเป็น YYYY-MM-DD)'
            }), 400
        
        db = get_session()
        
        try:
            # ตรวจสอบว่ามีสาขานี้อยู่หรือไม่
            branch = db.query(Branch).filter_by(branch_id=branch_id).first()
            if not branch:
                return jsonify({
                    'success': False,
                    'message': 'ไม่พบสาขา'
                }), 404
            
            # ดึงข้อมูลการนับลูกค้าตามวัน
            daily_counts = db.query(
                    func.date(CustomerCount.timestamp).label('date'),
                    func.sum(CustomerCount.entry_count).label('entries'),
                    func.sum(CustomerCount.exit_count).label('exits'),
                    func.max(CustomerCount.current_count).label('max_count')
                ) \
                .filter(and_(
                    CustomerCount.branch_id == branch_id,
                    CustomerCount.timestamp >= start_date,
                    CustomerCount.timestamp < end_date
                )) \
                .group_by('date') \
                .order_by('date') \
                .all()
            
            # สร้างข้อมูลรายงาน
            daily_data = []
            total_entries = 0
            total_exits = 0
            max_day_count = 0
            max_day = None
            
            for date, entries, exits, max_count in daily_counts:
                date_str = date.strftime('%Y-%m-%d')
                day_name = date.strftime('%A')  # ชื่อวัน (อังกฤษ)
                
                daily_data.append({
                    'date': date_str,
                    'day': day_name,
                    'entries': entries,
                    'exits': exits,
                    'max_count': max_count
                })
                
                total_entries += entries
                total_exits += exits
                
                if entries > max_day_count:
                    max_day_count = entries
                    max_day = day_name
            
            # สร้างข้อมูลสรุป
            summary = {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': (end_date - timedelta(days=1)).strftime('%Y-%m-%d'),
                'branch_id': branch_id,
                'branch_name': branch.name,
                'total_entries': total_entries,
                'total_exits': total_exits,
                'avg_daily_entries': round(total_entries / 7, 2) if daily_counts else 0,
                'max_concurrent': max(c[3] for c in daily_counts) if daily_counts else 0,
                'busiest_day': max_day,
                'busiest_day_count': max_day_count
            }
            
            # ส่งข้อมูลในรูปแบบที่ต้องการ
            if output_format == 'csv':
                # สร้างไฟล์ CSV
                csv_data = io.StringIO()
                csv_writer = csv.writer(csv_data)
                
                # เขียนส่วนหัว
                csv_writer.writerow(['รายงานประจำสัปดาห์', f"{summary['start_date']} ถึง {summary['end_date']}"])
                csv_writer.writerow(['สาขา', branch.branch_id, branch.name])
                csv_writer.writerow([])
                csv_writer.writerow(['วันที่', 'วัน', 'จำนวนลูกค้าเข้า', 'จำนวนลูกค้าออก', 'จำนวนลูกค้าสูงสุด'])
                
                # เขียนข้อมูลรายวัน
                for day_data in daily_data:
                    csv_writer.writerow([
                        day_data['date'],
                        day_data['day'],
                        day_data['entries'],
                        day_data['exits'],
                        day_data['max_count']
                    ])
                
                # เขียนสรุป
                csv_writer.writerow([])
                csv_writer.writerow(['สรุป'])
                csv_writer.writerow(['จำนวนลูกค้าเข้าทั้งหมด', summary['total_entries']])
                csv_writer.writerow(['จำนวนลูกค้าออกทั้งหมด', summary['total_exits']])
                csv_writer.writerow(['เฉลี่ยลูกค้าเข้าต่อวัน', summary['avg_daily_entries']])
                csv_writer.writerow(['จำนวนลูกค้าสูงสุด', summary['max_concurrent']])
                csv_writer.writerow(['วันที่มีลูกค้าเข้ามากที่สุด', summary['busiest_day']])
                csv_writer.writerow(['จำนวนลูกค้าในวันที่มากที่สุด', summary['busiest_day_count']])
                
                # สร้างไฟล์
                csv_data.seek(0)
                
                # สร้างชื่อไฟล์
                filename = f"weekly_report_{branch_id}_{summary['start_date']}_to_{summary['end_date']}.csv"
                
                # ส่งไฟล์
                return send_file(
                    io.BytesIO(csv_data.getvalue().encode()),
                    mimetype='text/csv',
                    as_attachment=True,
                    download_name=filename
                )
            else:
                # ส่งข้อมูลในรูปแบบ JSON
                return jsonify({
                    'success': True,
                    'report': {
                        'summary': summary,
                        'daily_data': daily_data
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
        logger.error(f"เกิดข้อผิดพลาดในการสร้างรายงานประจำสัปดาห์: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'เกิดข้อผิดพลาด: ' + str(e)
        }), 500

@reports_bp.route('/monthly/<branch_id>', methods=['GET'])
@token_required
def monthly_report(branch_id):
    """สร้างรายงานประจำเดือนของสาขา"""
    try:
        # ดึงพารามิเตอร์
        date_str = request.args.get('date', datetime.now().strftime('%Y-%m'))
        output_format = request.args.get('format', 'json')  # json, csv
        
        # แปลงวันที่
        try:
            if len(date_str) == 7:  # รูปแบบ YYYY-MM
                date_parts = date_str.split('-')
                year = int(date_parts[0])
                month = int(date_parts[1])
                
                # หาวันแรกและวันสุดท้ายของเดือน
                start_date = datetime(year, month, 1)
                if month == 12:
                    end_date = datetime(year + 1, 1, 1)
                else:
                    end_date = datetime(year, month + 1, 1)
            else:
                return jsonify({
                    'success': False,
                    'message': 'รูปแบบวันที่ไม่ถูกต้อง (ควรเป็น YYYY-MM)'
                }), 400
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'รูปแบบวันที่ไม่ถูกต้อง (ควรเป็น YYYY-MM)'
            }), 400
        
        db = get_session()
        
        try:
            # ตรวจสอบว่ามีสาขานี้อยู่หรือไม่
            branch = db.query(Branch).filter_by(branch_id=branch_id).first()
            if not branch:
                return jsonify({
                    'success': False,
                    'message': 'ไม่พบสาขา'
                }), 404
            
            # ดึงข้อมูลการนับลูกค้าตามวัน
            daily_counts = db.query(
                    func.date(CustomerCount.timestamp).label('date'),
                    func.sum(CustomerCount.entry_count).label('entries'),
                    func.sum(CustomerCount.exit_count).label('exits'),
                    func.max(CustomerCount.current_count).label('max_count')
                ) \
                .filter(and_(
                    CustomerCount.branch_id == branch_id,
                    CustomerCount.timestamp >= start_date,
                    CustomerCount.timestamp < end_date
                )) \
                .group_by('date') \
                .order_by('date') \
                .all()
            
            # สร้างข้อมูลรายงาน
            daily_data = []
            total_entries = 0
            total_exits = 0
            max_day_count = 0
            max_day = None
            
            for date, entries, exits, max_count in daily_counts:
                date_str = date.strftime('%Y-%m-%d')
                day_name = date.strftime('%A')  # ชื่อวัน (อังกฤษ)
                
                daily_data.append({
                    'date': date_str,
                    'day': day_name,
                    'entries': entries,
                    'exits': exits,
                    'max_count': max_count
                })
                
                total_entries += entries
                total_exits += exits
                
                if entries > max_day_count:
                    max_day_count = entries
                    max_day = date_str
            
            # สร้างข้อมูลสรุปรายสัปดาห์
            weekly_data = []
            
            # จัดกลุ่มข้อมูลตามสัปดาห์
            week_data = {}
            for item in daily_data:
                date_obj = datetime.strptime(item['date'], '%Y-%m-%d')
                week_num = date_obj.isocalendar()[1]  # เลขสัปดาห์
                
                if week_num not in week_data:
                    week_data[week_num] = {
                        'week': week_num,
                        'start_date': item['date'],
                        'end_date': item['date'],
                        'entries': 0,
                        'exits': 0,
                        'max_count': 0
                    }
                
                # อัพเดตข้อมูลสัปดาห์
                week_data[week_num]['entries'] += item['entries']
                week_data[week_num]['exits'] += item['exits']
                week_data[week_num]['max_count'] = max(week_data[week_num]['max_count'], item['max_count'])
                week_data[week_num]['end_date'] = item['date']
            
            # แปลงข้อมูลสัปดาห์เป็นรายการ
            for week_num in sorted(week_data.keys()):
                weekly_data.append(week_data[week_num])
            
            # หาสัปดาห์ที่มีลูกค้าเข้ามากที่สุด
            max_week_entries = 0
            max_week = None
            
            for week in weekly_data:
                if week['entries'] > max_week_entries:
                    max_week_entries = week['entries']
                    max_week = week['week']
            
            # สร้างข้อมูลสรุป
            days_in_month = (end_date - start_date).days
            summary = {
                'year': start_date.year,
                'month': start_date.month,
                'month_name': start_date.strftime('%B'),  # ชื่อเดือน (อังกฤษ)
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': (end_date - timedelta(days=1)).strftime('%Y-%m-%d'),
                'branch_id': branch_id,
                'branch_name': branch.name,
                'total_entries': total_entries,
                'total_exits': total_exits,
                'avg_daily_entries': round(total_entries / days_in_month, 2) if days_in_month > 0 else 0,
                'max_concurrent': max(c[3] for c in daily_counts) if daily_counts else 0,
                'busiest_day': max_day,
                'busiest_day_count': max_day_count,
                'busiest_week': max_week,
                'busiest_week_count': max_week_entries
            }
            
            # ส่งข้อมูลในรูปแบบที่ต้องการ
            if output_format == 'csv':
                # สร้างไฟล์ CSV
                csv_data = io.StringIO()
                csv_writer = csv.writer(csv_data)
                
                # เขียนส่วนหัว
                csv_writer.writerow(['รายงานประจำเดือน', f"{summary['month_name']} {summary['year']}"])
                csv_writer.writerow(['สาขา', branch.branch_id, branch.name])
                csv_writer.writerow([])
                
                # เขียนข้อมูลรายวัน
                csv_writer.writerow(['ข้อมูลรายวัน'])
                csv_writer.writerow(['วันที่', 'วัน', 'จำนวนลูกค้าเข้า', 'จำนวนลูกค้าออก', 'จำนวนลูกค้าสูงสุด'])
                
                for day_data in daily_data:
                    csv_writer.writerow([
                        day_data['date'],
                        day_data['day'],
                        day_data['entries'],
                        day_data['exits'],
                        day_data['max_count']
                    ])
                
                # เขียนข้อมูลรายสัปดาห์
                csv_writer.writerow([])
                csv_writer.writerow(['ข้อมูลรายสัปดาห์'])
                csv_writer.writerow(['สัปดาห์', 'วันที่เริ่ม', 'วันที่สิ้นสุด', 'จำนวนลูกค้าเข้า', 'จำนวนลูกค้าออก', 'จำนวนลูกค้าสูงสุด'])
                
                for week_data in weekly_data:
                    csv_writer.writerow([
                        week_data['week'],
                        week_data['start_date'],
                        week_data['end_date'],
                        week_data['entries'],
                        week_data['exits'],
                        week_data['max_count']
                    ])
                
                # เขียนสรุป
                csv_writer.writerow([])
                csv_writer.writerow(['สรุป'])
                csv_writer.writerow(['จำนวนลูกค้าเข้าทั้งหมด', summary['total_entries']])
                csv_writer.writerow(['จำนวนลูกค้าออกทั้งหมด', summary['total_exits']])
                csv_writer.writerow(['เฉลี่ยลูกค้าเข้าต่อวัน', summary['avg_daily_entries']])
                csv_writer.writerow(['จำนวนลูกค้าสูงสุด', summary['max_concurrent']])
                csv_writer.writerow(['วันที่มีลูกค้าเข้ามากที่สุด', summary['busiest_day']])
                csv_writer.writerow(['จำนวนลูกค้าในวันที่มากที่สุด', summary['busiest_day_count']])
                csv_writer.writerow(['สัปดาห์ที่มีลูกค้าเข้ามากที่สุด', summary['busiest_week']])
                csv_writer.writerow(['จำนวนลูกค้าในสัปดาห์ที่มากที่สุด', summary['busiest_week_count']])
                
                # สร้างไฟล์
                csv_data.seek(0)
                
                # สร้างชื่อไฟล์
                filename = f"monthly_report_{branch_id}_{start_date.strftime('%Y-%m')}.csv"
                
                # ส่งไฟล์
                return send_file(
                    io.BytesIO(csv_data.getvalue().encode()),
                    mimetype='text/csv',
                    as_attachment=True,
                    download_name=filename
                )
            else:
                # ส่งข้อมูลในรูปแบบ JSON
                return jsonify({
                    'success': True,
                    'report': {
                        'summary': summary,
                        'daily_data': daily_data,
                        'weekly_data': weekly_data
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
        logger.error(f"เกิดข้อผิดพลาดในการสร้างรายงานประจำเดือน: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'เกิดข้อผิดพลาด: ' + str(e)
        }), 500

@reports_bp.route('/comparison/<branch_id>', methods=['GET'])
@token_required
def comparison_report(branch_id):
    """สร้างรายงานเปรียบเทียบระหว่างสองช่วงเวลา"""
    try:
        # ดึงพารามิเตอร์
        period1_start = request.args.get('period1_start')
        period1_end = request.args.get('period1_end')
        period2_start = request.args.get('period2_start')
        period2_end = request.args.get('period2_end')
        output_format = request.args.get('format', 'json')  # json, csv
        
        # ตรวจสอบพารามิเตอร์
        if not all([period1_start, period1_end, period2_start, period2_end]):
            return jsonify({
                'success': False,
                'message': 'กรุณาระบุช่วงเวลาทั้งสองช่วง (period1_start, period1_end, period2_start, period2_end)'
            }), 400
        
        # แปลงวันที่
        try:
            period1_start_dt = datetime.strptime(period1_start, '%Y-%m-%d')
            period1_end_dt = datetime.strptime(period1_end, '%Y-%m-%d') + timedelta(days=1)
            period2_start_dt = datetime.strptime(period2_start, '%Y-%m-%d')
            period2_end_dt = datetime.strptime(period2_end, '%Y-%m-%d') + timedelta(days=1)
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'รูปแบบวันที่ไม่ถูกต้อง (ควรเป็น YYYY-MM-DD)'
            }), 400
        
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
            
            # สร้างข้อมูลผลลัพธ์
            result = {
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
            }
            
            # ส่งข้อมูลในรูปแบบที่ต้องการ
            if output_format == 'csv':
                # สร้างไฟล์ CSV
                csv_data = io.StringIO()
                csv_writer = csv.writer(csv_data)
                
                # เขียนส่วนหัว
                csv_writer.writerow(['รายงานเปรียบเทียบ', f"{branch.name} ({branch_id})"])
                csv_writer.writerow([])
                
                # เขียนข้อมูลทั้งสองช่วงเวลา
                csv_writer.writerow(['ช่วงเวลาที่ 1', period1_start, 'ถึง', period1_end])
                csv_writer.writerow(['จำนวนลูกค้าเข้า', period1_entries])
                csv_writer.writerow(['จำนวนลูกค้าออก', period1_exits])
                csv_writer.writerow(['จำนวนลูกค้าสูงสุด', period1_max])
                csv_writer.writerow([])
                
                csv_writer.writerow(['ช่วงเวลาที่ 2', period2_start, 'ถึง', period2_end])
                csv_writer.writerow(['จำนวนลูกค้าเข้า', period2_entries])
                csv_writer.writerow(['จำนวนลูกค้าออก', period2_exits])
                csv_writer.writerow(['จำนวนลูกค้าสูงสุด', period2_max])
                csv_writer.writerow([])
                
                # เขียนข้อมูลการเปลี่ยนแปลง
                csv_writer.writerow(['การเปลี่ยนแปลง (%)'])
                csv_writer.writerow(['จำนวนลูกค้าเข้า', f"{round(entries_change, 2)}%"])
                csv_writer.writerow(['จำนวนลูกค้าออก', f"{round(exits_change, 2)}%"])
                csv_writer.writerow(['จำนวนลูกค้าสูงสุด', f"{round(max_change, 2)}%"])
                
                # สร้างไฟล์
                csv_data.seek(0)
                
                # สร้างชื่อไฟล์
                filename = f"comparison_report_{branch_id}_{period1_start}_vs_{period2_start}.csv"
                
                # ส่งไฟล์
                return send_file(
                    io.BytesIO(csv_data.getvalue().encode()),
                    mimetype='text/csv',
                    as_attachment=True,
                    download_name=filename
                )
            else:
                # ส่งข้อมูลในรูปแบบ JSON
                return jsonify(result)
        
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
        logger.error(f"เกิดข้อผิดพลาดในการสร้างรายงานเปรียบเทียบ: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'เกิดข้อผิดพลาด: ' + str(e)
        }), 500
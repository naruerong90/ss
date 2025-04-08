# web/routes.py - ตั้งค่า URL routes สำหรับเว็บแอปพลิเคชัน
import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.security import check_password_hash
from server.db import get_session
from models.user import User
from models.branch import Branch
from models.customer_count import CustomerCount
from sqlalchemy import func, desc
from datetime import datetime, timedelta
import json

# สร้าง Blueprint
web_bp = Blueprint('web', __name__)

logger = logging.getLogger(__name__)

# Middleware สำหรับตรวจสอบการล็อกอิน
def login_required(f):
    """
    Decorator ตรวจสอบการล็อกอิน
    
    Args:
        f: ฟังก์ชันที่จะตรวจสอบการล็อกอิน
        
    Returns:
        wrapper: ฟังก์ชันที่ครอบด้วยการตรวจสอบการล็อกอิน
    """
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash('กรุณาล็อกอินก่อน', 'warning')
            return redirect(url_for('web.login', next=request.path))
        return f(*args, **kwargs)
    
    wrapper.__name__ = f.__name__
    return wrapper

# Middleware สำหรับตรวจสอบสิทธิ์ admin
def admin_required(f):
    """
    Decorator ตรวจสอบสิทธิ์ admin
    
    Args:
        f: ฟังก์ชันที่จะตรวจสอบสิทธิ์ admin
        
    Returns:
        wrapper: ฟังก์ชันที่ครอบด้วยการตรวจสอบสิทธิ์ admin
    """
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash('กรุณาล็อกอินก่อน', 'warning')
            return redirect(url_for('web.login', next=request.path))
        
        if not session.get('is_admin', False):
            flash('ต้องมีสิทธิ์ admin เท่านั้น', 'danger')
            return redirect(url_for('web.dashboard'))
        
        return f(*args, **kwargs)
    
    wrapper.__name__ = f.__name__
    return wrapper

@web_bp.route('/')
def index():
    """หน้าแรก"""
    if 'user_id' in session:
        return redirect(url_for('web.dashboard'))
    
    return render_template('index.html')

@web_bp.route('/login', methods=['GET', 'POST'])
def login():
    """หน้าล็อกอิน"""
    if 'user_id' in session:
        return redirect(url_for('web.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        db = get_session()
        
        try:
            # ดึงข้อมูลผู้ใช้
            user = db.query(User).filter_by(username=username).first()
            
            # ตรวจสอบรหัสผ่าน
            if user and user.check_password(password):
                # ตรวจสอบว่าผู้ใช้ยังใช้งานอยู่หรือไม่
                if not user.is_active:
                    flash('บัญชีผู้ใช้นี้ถูกระงับการใช้งาน', 'danger')
                    return render_template('login.html')
                
                # บันทึกข้อมูลการล็อกอินลงใน session
                session['user_id'] = user.id
                session['username'] = user.username
                session['name'] = user.name
                session['is_admin'] = user.is_admin
                
                # อัพเดตเวลาเข้าสู่ระบบล่าสุด
                user.last_login = datetime.now()
                db.commit()
                
                # ไปยังหน้าที่ต้องการหลังจากล็อกอิน
                next_url = request.args.get('next', url_for('web.dashboard'))
                return redirect(next_url)
            else:
                flash('ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง', 'danger')
                return render_template('login.html')
        
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการล็อกอิน: {str(e)}")
            flash('เกิดข้อผิดพลาดในการล็อกอิน', 'danger')
            return render_template('login.html')
        
        finally:
            db.close()
    
    return render_template('login.html')

@web_bp.route('/logout')
def logout():
    """ออกจากระบบ"""
    # ลบข้อมูลการล็อกอินออกจาก session
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('name', None)
    session.pop('is_admin', None)
    
    flash('ออกจากระบบสำเร็จ', 'success')
    return redirect(url_for('web.login'))

@web_bp.route('/dashboard')
@login_required
def dashboard():
    """หน้า Dashboard"""
    db = get_session()
    
    try:
        # ดึงข้อมูลสาขาทั้งหมด
        branches = db.query(Branch).all()
        
        # ดึงข้อมูลการนับลูกค้าล่าสุดของแต่ละสาขา
        branch_data = []
        for branch in branches:
            # ดึงข้อมูลการนับลูกค้าล่าสุด
            latest_counts = db.query(
                    CustomerCount.timestamp,
                    func.sum(CustomerCount.entry_count).label('entries'),
                    func.sum(CustomerCount.exit_count).label('exits')
                ) \
                .filter(
                    CustomerCount.branch_id == branch.branch_id,
                    CustomerCount.timestamp >= datetime.now() - timedelta(days=1)
                ) \
                .group_by(func.date(CustomerCount.timestamp), func.hour(CustomerCount.timestamp)) \
                .order_by(desc(CustomerCount.timestamp)) \
                .limit(24) \
                .all()
            
            # สร้างข้อมูลสำหรับกราฟ
            chart_data = []
            for timestamp, entries, exits in latest_counts:
                chart_data.append({
                    'timestamp': timestamp.strftime('%H:%M'),
                    'entries': entries,
                    'exits': exits
                })
            
            # สร้างข้อมูลสาขา
            branch_data.append({
                'id': branch.id,
                'branch_id': branch.branch_id,
                'name': branch.name,
                'current_count': branch.current_customer_count,
                'capacity': branch.capacity,
                'last_updated': branch.last_updated.strftime('%Y-%m-%d %H:%M:%S') if branch.last_updated else 'ไม่มีข้อมูล',
                'chart_data': json.dumps(chart_data[::-1])  # กลับด้านให้เวลาเรียงจากน้อยไปมาก
            })
        
        return render_template('dashboard.html', branches=branch_data)
    
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการดึงข้อมูลสำหรับ dashboard: {str(e)}")
        flash('เกิดข้อผิดพลาดในการดึงข้อมูล', 'danger')
        return render_template('dashboard.html', branches=[])
    
    finally:
        db.close()

@web_bp.route('/branch/<branch_id>')
@login_required
def branch_detail(branch_id):
    """หน้ารายละเอียดสาขา"""
    db = get_session()
    
    try:
        # ดึงข้อมูลสาขา
        branch = db.query(Branch).filter_by(branch_id=branch_id).first()
        
        if not branch:
            flash('ไม่พบข้อมูลสาขา', 'danger')
            return redirect(url_for('web.dashboard'))
        
        # ดึงข้อมูลการนับลูกค้าของสาขานี้
        counts_by_hour = db.query(
                func.date(CustomerCount.timestamp).label('date'),
                func.hour(CustomerCount.timestamp).label('hour'),
                func.sum(CustomerCount.entry_count).label('entries'),
                func.sum(CustomerCount.exit_count).label('exits'),
                func.max(CustomerCount.current_count).label('max_count')
            ) \
            .filter(
                CustomerCount.branch_id == branch_id,
                CustomerCount.timestamp >= datetime.now() - timedelta(days=7)
            ) \
            .group_by('date', 'hour') \
            .order_by('date', 'hour') \
            .all()
        
        # สร้างข้อมูลกราฟรายชั่วโมง
        hourly_chart_data = []
        for date, hour, entries, exits, max_count in counts_by_hour:
            hourly_chart_data.append({
                'datetime': f"{date} {hour:02d}:00",
                'entries': entries,
                'exits': exits,
                'max_count': max_count
            })
        
        # ดึงข้อมูลการนับลูกค้ารายวัน
        counts_by_day = db.query(
                func.date(CustomerCount.timestamp).label('date'),
                func.sum(CustomerCount.entry_count).label('entries'),
                func.sum(CustomerCount.exit_count).label('exits'),
                func.max(CustomerCount.current_count).label('max_count')
            ) \
            .filter(
                CustomerCount.branch_id == branch_id,
                CustomerCount.timestamp >= datetime.now() - timedelta(days=30)
            ) \
            .group_by('date') \
            .order_by('date') \
            .all()
        
        # สร้างข้อมูลกราฟรายวัน
        daily_chart_data = []
        for date, entries, exits, max_count in counts_by_day:
            daily_chart_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'entries': entries,
                'exits': exits,
                'max_count': max_count
            })
        
        return render_template(
            'branch_detail.html',
            branch=branch,
            hourly_chart_data=json.dumps(hourly_chart_data),
            daily_chart_data=json.dumps(daily_chart_data)
        )
    
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการดึงข้อมูลสาขา: {str(e)}")
        flash('เกิดข้อผิดพลาดในการดึงข้อมูล', 'danger')
        return redirect(url_for('web.dashboard'))
    
    finally:
        db.close()

@web_bp.route('/snapshots/<branch_id>')
@login_required
def snapshots(branch_id):
    """หน้าภาพสแนปช็อตของสาขา"""
    from models.snapshot import Snapshot
    
    db = get_session()
    
    try:
        # ดึงข้อมูลสาขา
        branch = db.query(Branch).filter_by(branch_id=branch_id).first()
        
        if not branch:
            flash('ไม่พบข้อมูลสาขา', 'danger')
            return redirect(url_for('web.dashboard'))
        
        # ดึงภาพสแนปช็อตล่าสุด
        snapshots = db.query(Snapshot) \
            .filter_by(branch_id=branch_id) \
            .order_by(desc(Snapshot.timestamp)) \
            .limit(20) \
            .all()
        
        # แปลงข้อมูลเป็นรูปแบบที่เหมาะสม
        snapshot_data = []
        for snapshot in snapshots:
            snapshot_data.append({
                'id': snapshot.id,
                'camera_id': snapshot.camera_id,
                'timestamp': snapshot.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'url': url_for('web.view_snapshot', snapshot_id=snapshot.id),
                'current_count': snapshot.current_count,
                'reason': snapshot.reason
            })
        
        return render_template(
            'snapshots.html',
            branch=branch,
            snapshots=snapshot_data
        )
    
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการดึงข้อมูลภาพสแนปช็อต: {str(e)}")
        flash('เกิดข้อผิดพลาดในการดึงข้อมูล', 'danger')
        return redirect(url_for('web.dashboard'))
    
    finally:
        db.close()

@web_bp.route('/snapshot/<int:snapshot_id>')
@login_required
def view_snapshot(snapshot_id):
    """ดูภาพสแนปช็อต"""
    from models.snapshot import Snapshot
    import os
    
    db = get_session()
    
    try:
        # ดึงข้อมูลสแนปช็อต
        snapshot = db.query(Snapshot).filter_by(id=snapshot_id).first()
        
        if not snapshot:
            flash('ไม่พบภาพสแนปช็อต', 'danger')
            return redirect(url_for('web.dashboard'))
        
        # สร้างพาธไปยังไฟล์
        snapshot_folder = current_app.config['SNAPSHOT_FOLDER']
        file_path = os.path.join(snapshot_folder, snapshot.filename)
        
        # ตรวจสอบว่าไฟล์มีอยู่หรือไม่
        if not os.path.exists(file_path):
            flash('ไม่พบไฟล์ภาพสแนปช็อต', 'danger')
            return redirect(url_for('web.dashboard'))
        
        # ส่งไฟล์
        return send_file(file_path, mimetype='image/jpeg')
    
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการดูภาพสแนปช็อต: {str(e)}")
        flash('เกิดข้อผิดพลาดในการดูภาพสแนปช็อต', 'danger')
        return redirect(url_for('web.dashboard'))
    
    finally:
        db.close()

# หน้าสำหรับผู้ดูแลระบบ
@web_bp.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    """หน้า Dashboard สำหรับผู้ดูแลระบบ"""
    db = get_session()
    
    try:
        # ดึงข้อมูลสาขาทั้งหมด
        branches_count = db.query(func.count(Branch.id)).scalar()
        
        # ดึงข้อมูลผู้ใช้ทั้งหมด
        users_count = db.query(func.count(User.id)).scalar()
        
        # ดึงข้อมูลลูกค้าทั้งหมดในวันนี้
        today = datetime.now().date()
        today_counts = db.query(
                func.sum(CustomerCount.entry_count).label('entries'),
                func.sum(CustomerCount.exit_count).label('exits')
            ) \
            .filter(func.date(CustomerCount.timestamp) == today) \
            .first()
        
        today_entries = today_counts.entries or 0
        today_exits = today_counts.exits or 0
        
        # ดึงข้อมูลการนับลูกค้ารายวันในเดือนนี้
        start_of_month = datetime(today.year, today.month, 1)
        counts_by_day = db.query(
                func.date(CustomerCount.timestamp).label('date'),
                func.sum(CustomerCount.entry_count).label('entries')
            ) \
            .filter(CustomerCount.timestamp >= start_of_month) \
            .group_by('date') \
            .order_by('date') \
            .all()
        
        # สร้างข้อมูลกราฟรายวัน
        daily_chart_data = []
        for date, entries in counts_by_day:
            daily_chart_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'entries': entries
            })
        
        return render_template(
            'admin/dashboard.html',
            branches_count=branches_count,
            users_count=users_count,
            today_entries=today_entries,
            today_exits=today_exits,
            daily_chart_data=json.dumps(daily_chart_data)
        )
    
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการดึงข้อมูลสำหรับ admin dashboard: {str(e)}")
        flash('เกิดข้อผิดพลาดในการดึงข้อมูล', 'danger')
        return render_template('admin/dashboard.html')
    
    finally:
        db.close()

@web_bp.route('/admin/branches')
@login_required
@admin_required
def admin_branches():
    """หน้าจัดการสาขา"""
    db = get_session()
    
    try:
        # ดึงข้อมูลสาขาทั้งหมด
        branches = db.query(Branch).all()
        
        return render_template('admin/branches.html', branches=branches)
    
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการดึงข้อมูลสาขา: {str(e)}")
        flash('เกิดข้อผิดพลาดในการดึงข้อมูล', 'danger')
        return render_template('admin/branches.html', branches=[])
    
    finally:
        db.close()

@web_bp.route('/admin/users')
@login_required
@admin_required
def admin_users():
    """หน้าจัดการผู้ใช้"""
    db = get_session()
    
    try:
        # ดึงข้อมูลผู้ใช้ทั้งหมด
        users = db.query(User).all()
        
        return render_template('admin/users.html', users=users)
    
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการดึงข้อมูลผู้ใช้: {str(e)}")
        flash('เกิดข้อผิดพลาดในการดึงข้อมูล', 'danger')
        return render_template('admin/users.html', users=[])
    
    finally:
        db.close()

@web_bp.route('/admin/devices')
@login_required
@admin_required
def admin_devices():
    """หน้าจัดการอุปกรณ์"""
    from models.device import Device
    
    db = get_session()
    
    try:
        # ดึงข้อมูลอุปกรณ์ทั้งหมด
        devices = db.query(Device).all()
        
        # แปลงข้อมูลเป็นรูปแบบที่เหมาะสม
        device_data = []
        for device in devices:
            device_data.append({
                'id': device.id,
                'device_id': device.device_id,
                'camera_id': device.camera_id,
                'branch_id': device.branch_id,
                'ip_address': device.ip_address,
                'registration_date': device.registration_date.strftime('%Y-%m-%d %H:%M:%S'),
                'last_seen': device.last_seen.strftime('%Y-%m-%d %H:%M:%S'),
                'status': device.status,
                'version': device.version,
                'metadata': json.loads(device.metadata) if device.metadata else {}
            })
        
        return render_template('admin/devices.html', devices=device_data)
    
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการดึงข้อมูลอุปกรณ์: {str(e)}")
        flash('เกิดข้อผิดพลาดในการดึงข้อมูล', 'danger')
        return render_template('admin/devices.html', devices=[])
    
    finally:
        db.close()

@web_bp.route('/profile')
@login_required
def profile():
    """หน้าโปรไฟล์ผู้ใช้"""
    db = get_session()
    
    try:
        # ดึงข้อมูลผู้ใช้
        user = db.query(User).filter_by(id=session['user_id']).first()
        
        if not user:
            flash('ไม่พบข้อมูลผู้ใช้', 'danger')
            return redirect(url_for('web.logout'))
        
        return render_template('profile.html', user=user)
    
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการดึงข้อมูลโปรไฟล์: {str(e)}")
        flash('เกิดข้อผิดพลาดในการดึงข้อมูล', 'danger')
        return redirect(url_for('web.dashboard'))
    
    finally:
        db.close()

@web_bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    """อัพเดตโปรไฟล์ผู้ใช้"""
    db = get_session()
    
    try:
        # ดึงข้อมูลผู้ใช้
        user = db.query(User).filter_by(id=session['user_id']).first()
        
        if not user:
            flash('ไม่พบข้อมูลผู้ใช้', 'danger')
            return redirect(url_for('web.logout'))
        
        # อัพเดตข้อมูลผู้ใช้
        user.name = request.form.get('name', user.name)
        user.email = request.form.get('email', user.email)
        user.phone = request.form.get('phone', user.phone)
        
        db.commit()
        
        # อัพเดต session
        session['name'] = user.name
        
        flash('อัพเดตข้อมูลสำเร็จ', 'success')
        return redirect(url_for('web.profile'))
    
    except Exception as e:
        db.rollback()
        logger.error(f"เกิดข้อผิดพลาดในการอัพเดตข้อมูลโปรไฟล์: {str(e)}")
        flash('เกิดข้อผิดพลาดในการอัพเดตข้อมูล', 'danger')
        return redirect(url_for('web.profile'))
    
    finally:
        db.close()

@web_bp.route('/profile/change-password', methods=['POST'])
@login_required
def change_password():
    """เปลี่ยนรหัสผ่านผู้ใช้"""
    db = get_session()
    
    try:
        # ดึงข้อมูลผู้ใช้
        user = db.query(User).filter_by(id=session['user_id']).first()
        
        if not user:
            flash('ไม่พบข้อมูลผู้ใช้', 'danger')
            return redirect(url_for('web.logout'))
        
        # ตรวจสอบรหัสผ่านปัจจุบัน
        current_password = request.form.get('current_password')
        if not user.check_password(current_password):
            flash('รหัสผ่านปัจจุบันไม่ถูกต้อง', 'danger')
            return redirect(url_for('web.profile'))
        
        # ตรวจสอบรหัสผ่านใหม่
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if new_password != confirm_password:
            flash('รหัสผ่านใหม่ไม่ตรงกัน', 'danger')
            return redirect(url_for('web.profile'))
        
        if len(new_password) < 8:
            flash('รหัสผ่านใหม่ต้องมีความยาวอย่างน้อย 8 ตัวอักษร', 'danger')
            return redirect(url_for('web.profile'))
        
        # อัพเดตรหัสผ่าน
        user.set_password(new_password)
        db.commit()
        
        flash('เปลี่ยนรหัสผ่านสำเร็จ', 'success')
        return redirect(url_for('web.profile'))
    
    except Exception as e:
        db.rollback()
        logger.error(f"เกิดข้อผิดพลาดในการเปลี่ยนรหัสผ่าน: {str(e)}")
        flash('เกิดข้อผิดพลาดในการเปลี่ยนรหัสผ่าน', 'danger')
        return redirect(url_for('web.profile'))
    
    finally:
        db.close()

@web_bp.route('/reports')
@login_required
def reports():
    """หน้ารายงาน"""
    return render_template('reports.html')

@web_bp.route('/settings')
@login_required
@admin_required
def settings():
    """หน้าตั้งค่าระบบ"""
    return render_template('admin/settings.html')
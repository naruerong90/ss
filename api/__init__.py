# api/v1/__init__.py - นำเข้า blueprints ทั้งหมดจาก API v1

# นำเข้าโมดูลพื้นฐาน
import logging

# ตั้งค่า logger สำหรับ API v1
logger = logging.getLogger(__name__)

# API version
__version__ = '1.0.0'

# นำเข้า blueprint จากไฟล์ต่างๆ
from api.v1.branches_bp import branches_bp
from api.v1.customer_counts_bp import customer_counts_bp
from api.v1.snapshots_bp import snapshots_bp
from api.v1.devices_bp import devices_bp
from api.v1.reports_bp import reports_bp
from api.v1.auth_bp import auth_bp

# สร้าง Blueprint สำหรับโมดูลที่ยังไม่ได้สร้าง
from flask import Blueprint, jsonify

# สร้าง blueprint ชั่วคราวสำหรับ API ที่ยังไม่ได้พัฒนา
customers_bp = Blueprint('customers', __name__)
employees_bp = Blueprint('employees', __name__)
appointments_bp = Blueprint('appointments', __name__)
updates_bp = Blueprint('updates', __name__)

@customers_bp.route('', methods=['GET'])
def get_customers():
    return jsonify({
        'success': True,
        'message': 'API สำหรับลูกค้ายังไม่ได้พัฒนา'
    })

@employees_bp.route('', methods=['GET'])
def get_employees():
    return jsonify({
        'success': True,
        'message': 'API สำหรับพนักงานยังไม่ได้พัฒนา'
    })

@appointments_bp.route('', methods=['GET'])
def get_appointments():
    return jsonify({
        'success': True,
        'message': 'API สำหรับการนัดหมายยังไม่ได้พัฒนา'
    })

@updates_bp.route('', methods=['GET'])
def get_updates():
    return jsonify({
        'success': True,
        'message': 'API สำหรับการอัพเดตยังไม่ได้พัฒนา'
    })

# รวม blueprints ทั้งหมดสำหรับ API v1
all_blueprints = [
    branches_bp, 
    customers_bp, 
    employees_bp, 
    appointments_bp, 
    customer_counts_bp, 
    snapshots_bp, 
    reports_bp, 
    updates_bp, 
    devices_bp,
    auth_bp
]
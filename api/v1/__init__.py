# api/v1/__init__.py - นำเข้า blueprints ทั้งหมด
from api.v1.devices_bp import devices_bp
from api.v1.customer_counts_bp import customer_counts_bp
from api.v1.snapshots_bp import snapshots_bp

# สร้าง blueprints สำหรับ API อื่นๆ ที่ยังไม่ได้สร้าง
from flask import Blueprint, jsonify

# สร้าง blueprint ชั่วคราวสำหรับ API ที่ยังไม่ได้พัฒนา
branches_bp = Blueprint('branches', __name__)
customers_bp = Blueprint('customers', __name__)
employees_bp = Blueprint('employees', __name__)
appointments_bp = Blueprint('appointments', __name__)
reports_bp = Blueprint('reports', __name__)
updates_bp = Blueprint('updates', __name__)

@branches_bp.route('', methods=['GET'])
def get_branches():
    return jsonify({
        'success': True,
        'message': 'API สำหรับสาขายังไม่ได้พัฒนา'
    })

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

@reports_bp.route('', methods=['GET'])
def get_reports():
    return jsonify({
        'success': True,
        'message': 'API สำหรับรายงานยังไม่ได้พัฒนา'
    })

@updates_bp.route('', methods=['GET'])
def get_updates():
    return jsonify({
        'success': True,
        'message': 'API สำหรับการอัพเดตยังไม่ได้พัฒนา'
    })
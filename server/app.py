# server/app.py - สร้างแอปพลิเคชัน Flask
import os
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

logger = logging.getLogger(__name__)

def create_app(config):
    """
    สร้างและตั้งค่าแอปพลิเคชัน Flask
    
    Args:
        config: อ็อบเจกต์ ConfigParser ที่มีการตั้งค่า
        
    Returns:
        แอปพลิเคชัน Flask ที่ตั้งค่าแล้ว
    """
    app = Flask(__name__, 
                static_folder="../web/static",
                template_folder="../web/templates")
    
    # ตั้งค่า Flask
    app.config["SECRET_KEY"] = config.get("server", "secret_key")
    app.config["JSON_AS_ASCII"] = False
    app.config["UPLOAD_FOLDER"] = config.get("app", "upload_folder")
    app.config["SNAPSHOT_FOLDER"] = config.get("app", "snapshot_folder")
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB max upload
    
    # ตั้งค่า CORS
    allowed_origins = config.get("server", "allowed_origins")
    CORS(app, resources={r"/api/*": {"origins": allowed_origins.split(",")}})
    
    # ตั้งค่า ProxyFix สำหรับการทำงานหลัง reverse proxy
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    
    # ลงทะเบียน blueprints
    register_blueprints(app)
    
    # ลงทะเบียน error handlers
    register_error_handlers(app)
    
    # ลงทะเบียน hooks
    register_hooks(app)
    
    logger.info("สร้างแอปพลิเคชัน Flask เสร็จสมบูรณ์")
    
    return app

def register_blueprints(app):
    """ลงทะเบียน blueprints ทั้งหมด"""
    # นำเข้าเฉพาะเมื่อจำเป็น เพื่อหลีกเลี่ยง circular imports
    from api.v1 import (
        branches_bp, customers_bp, employees_bp, appointments_bp,
        customer_counts_bp, snapshots_bp, reports_bp, updates_bp,
        devices_bp
    )
    from web.routes import web_bp
    
    # ลงทะเบียน API blueprints
    api_prefix = "/api/v1"
    app.register_blueprint(branches_bp, url_prefix=f"{api_prefix}/branches")
    app.register_blueprint(customers_bp, url_prefix=f"{api_prefix}/customers")
    app.register_blueprint(employees_bp, url_prefix=f"{api_prefix}/employees")
    app.register_blueprint(appointments_bp, url_prefix=f"{api_prefix}/appointments")
    app.register_blueprint(customer_counts_bp, url_prefix=f"{api_prefix}/traffic")
    app.register_blueprint(snapshots_bp, url_prefix=f"{api_prefix}/snapshots")
    app.register_blueprint(reports_bp, url_prefix=f"{api_prefix}/reports")
    app.register_blueprint(updates_bp, url_prefix=f"{api_prefix}/updates")
    app.register_blueprint(devices_bp, url_prefix=f"{api_prefix}/devices")
    
    # ลงทะเบียน Web blueprint
    app.register_blueprint(web_bp)
    
    logger.info("ลงทะเบียน blueprints เสร็จสมบูรณ์")

def register_error_handlers(app):
    """ลงทะเบียนตัวจัดการข้อผิดพลาดทั้งหมด"""
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"error": "Bad Request", "message": str(error)}), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({"error": "Unauthorized", "message": "Authentication required"}), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({"error": "Forbidden", "message": "You don't have permission to access this resource"}), 403
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not Found", "message": "The requested resource was not found"}), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({"error": "Method Not Allowed", "message": "The method is not allowed for the requested URL"}), 405
    
    @app.errorhandler(500)
    def internal_server_error(error):
        logger.error(f"Internal Server Error: {error}")
        return jsonify({"error": "Internal Server Error", "message": "Something went wrong on the server"}), 500
    
    logger.info("ลงทะเบียนตัวจัดการข้อผิดพลาดเสร็จสมบูรณ์")

def register_hooks(app):
    """ลงทะเบียน hooks ทั้งหมด"""
    
    @app.before_request
    def before_request():
        # นำเข้าเฉพาะเมื่อจำเป็น เพื่อหลีกเลี่ยง circular imports
        from flask import request
        logger.debug(f"ได้รับคำขอ: {request.method} {request.path}")
    
    @app.after_request
    def after_request(response):
        # นำเข้าเฉพาะเมื่อจำเป็น เพื่อหลีกเลี่ยง circular imports
        from flask import request
        logger.debug(f"ส่งการตอบกลับ: {request.method} {request.path} - {response.status_code}")
        return response
    
    logger.info("ลงทะเบียน hooks เสร็จสมบูรณ์")
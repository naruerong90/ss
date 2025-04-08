# get_database_uri.py - สร้าง URI สำหรับการเชื่อมต่อฐานข้อมูล
import os

def get_database_uri(config):
    """
    สร้าง URI สำหรับเชื่อมต่อฐานข้อมูล
    
    Args:
        config: อ็อบเจกต์ ConfigParser ที่มีการตั้งค่าฐานข้อมูล
        
    Returns:
        URI สำหรับเชื่อมต่อฐานข้อมูล
    """
    db_type = config.get('database', 'type')
    db_name = config.get('database', 'name')
    
    if db_type == 'sqlite':
        db_path = config.get('database', 'path')
        db_file = os.path.join(db_path, db_name)
        return f"sqlite:///{db_file}"
    
    elif db_type == 'mysql':
        db_user = config.get('database', 'user')
        db_pass = config.get('database', 'password')
        db_host = config.get('database', 'host')
        db_port = config.get('database', 'port')
        return f"mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    
    elif db_type == 'postgresql':
        db_user = config.get('database', 'user')
        db_pass = config.get('database', 'password')
        db_host = config.get('database', 'host')
        db_port = config.get('database', 'port')
        return f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    
    else:
        raise ValueError(f"ไม่รองรับประเภทฐานข้อมูล: {db_type}")

# ตัวอย่างการใช้งาน (ถ้ารันไฟล์นี้โดยตรง)
if __name__ == "__main__":
    from configparser import ConfigParser
    
    # สร้างตัวอย่าง config
    config = ConfigParser()
    config['database'] = {
        'type': 'sqlite',
        'name': 'shop_counter.db',
        'path': 'data',
        'user': '',
        'password': '',
        'host': '',
        'port': ''
    }
    
    # ทดสอบการทำงาน
    uri = get_database_uri(config)
    print(f"ได้ URI ของฐานข้อมูล: {uri}")
from database import SessionLocal
from models import User, RawMaterial, Product


def init_data():
    db = SessionLocal()
    try:
        # Create default admin (李伟/老李) if not exist
        if db.query(User).count() == 0:
            users = [
                User(phone="17800105531", display_name="李伟", roles='["boss"]', status="approved"),
            ]
            db.add_all(users)

        # Create default raw materials
        if db.query(RawMaterial).count() == 0:
            materials = [
                RawMaterial(name="黑巧克力", category="巧克力类", unit="kg", current_stock=50, safety_stock=10, supplier="供应商A"),
                RawMaterial(name="白巧克力", category="巧克力类", unit="kg", current_stock=30, safety_stock=8, supplier="供应商A"),
                RawMaterial(name="可可脂", category="巧克力类", unit="kg", current_stock=20, safety_stock=5),
                RawMaterial(name="淡奶油", category="乳制品", unit="桶", current_stock=15, safety_stock=5),
                RawMaterial(name="奶油芝士", category="乳制品", unit="kg", current_stock=25, safety_stock=8),
                RawMaterial(name="马斯卡彭", category="乳制品", unit="kg", current_stock=10, safety_stock=3),
                RawMaterial(name="草莓果浆", category="果酱类", unit="kg", current_stock=40, safety_stock=10),
                RawMaterial(name="蓝莓果浆", category="果酱类", unit="kg", current_stock=35, safety_stock=10),
                RawMaterial(name="芒果果浆", category="果酱类", unit="kg", current_stock=30, safety_stock=8),
                RawMaterial(name="百香果果浆", category="果酱类", unit="kg", current_stock=20, safety_stock=5),
                RawMaterial(name="葡萄糖浆", category="糖浆类", unit="桶", current_stock=12, safety_stock=3),
                RawMaterial(name="麦芽糖浆", category="糖浆类", unit="桶", current_stock=8, safety_stock=2),
                RawMaterial(name="黄油", category="油脂类", unit="kg", current_stock=30, safety_stock=10),
                RawMaterial(name="椰子油", category="油脂类", unit="瓶", current_stock=15, safety_stock=5),
                RawMaterial(name="吉利丁片", category="添加剂", unit="袋", current_stock=50, safety_stock=15),
                RawMaterial(name="吉利丁粉", category="添加剂", unit="袋", current_stock=40, safety_stock=10),
                RawMaterial(name="低筋面粉", category="粉类", unit="袋", current_stock=20, safety_stock=5),
                RawMaterial(name="杏仁粉", category="粉类", unit="袋", current_stock=15, safety_stock=5),
                RawMaterial(name="抹茶粉", category="粉类", unit="袋", current_stock=8, safety_stock=2),
            ]
            db.add_all(materials)

        # Create default products
        if db.query(Product).count() == 0:
            products = [
                Product(name="黑巧克力慕斯", category="慕斯", unit="盒", current_stock=100),
                Product(name="白巧克力慕斯", category="慕斯", unit="盒", current_stock=80),
                Product(name="草莓慕斯", category="慕斯", unit="盒", current_stock=60),
                Product(name="芒果慕斯", category="慕斯", unit="盒", current_stock=50),
                Product(name="抹茶慕斯", category="慕斯", unit="盒", current_stock=40),
                Product(name="草莓果酱", category="果酱", unit="瓶", current_stock=200),
                Product(name="蓝莓果酱", category="果酱", unit="瓶", current_stock=150),
                Product(name="芒果果酱", category="果酱", unit="瓶", current_stock=120),
                Product(name="黑巧克力排块", category="巧克力", unit="盒", current_stock=80),
                Product(name="手工松露巧克力", category="巧克力", unit="盒", current_stock=60),
            ]
            db.add_all(products)

        db.commit()
        print("初始化数据完成")
    finally:
        db.close()

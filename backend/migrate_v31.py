"""
v3.1 一次性迁移：批次追溯四新表 + products 加列（user_version 3→4）

新表（create_all 也会建，但本脚本保证老库升级时按序执行 + 版本门闩防重复）：
  - material_batches（原料批次，UNIQUE(material_id, batch_no)）
  - batch_usages（批次消耗明细）
  - return_records（退货预埋 v3.2）
存量列：products.production_batch_no_prefix

存量数据策略（规格1.0节）：19原料/10产品/0生产/0发货，全部走"未分批"兼容层，零回填。

用法（backend/ 目录，先停服务）：
    sudo systemctl stop wuai-factory
    python3 migrate_v31.py
    sudo systemctl start wuai-factory
"""
import os
import shutil
import sqlite3
import sys
from datetime import datetime

DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "..", "data", "wuai.db"))

NEW_TABLES = ["material_batches", "batch_usages", "return_records"]
NEW_COLUMNS = [("products", "production_batch_no_prefix", "TEXT")]

VERSION = 4


def main():
    db_path = os.path.abspath(DB_PATH)
    if not os.path.exists(db_path):
        print(f"数据库不存在: {db_path}")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    try:
        current_version = conn.execute("PRAGMA user_version").fetchone()[0]
        if current_version >= VERSION:
            print(f"user_version={current_version}，已迁移过，跳过。")
            return
        if current_version < 3:
            print(f"user_version={current_version} < 3：请先执行 migrate_v3.py（时区迁移），再跑本脚本。")
            sys.exit(1)

        # 备份
        backup_dir = os.path.join(os.path.dirname(db_path), "..", "backups")
        os.makedirs(backup_dir, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"wuai_{stamp}.db")
        shutil.copy2(db_path, backup_path)
        print(f"已备份: {backup_path}")

        # 1. 新表（IF NOT EXISTS 与 create_all 幂等一致）
        conn.execute("""
            CREATE TABLE IF NOT EXISTS material_batches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                material_id INTEGER NOT NULL REFERENCES raw_materials(id),
                batch_no TEXT NOT NULL,
                quantity_in REAL NOT NULL,
                quantity_remaining REAL NOT NULL,
                unit_price REAL,
                production_date DATE,
                expiry_date DATE,
                supplier_id INTEGER REFERENCES suppliers(id),
                status TEXT DEFAULT '在库',
                notes TEXT,
                created_at DATETIME
            )
        """)
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_batch_material_no ON material_batches(material_id, batch_no)")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS batch_usages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                production_id INTEGER NOT NULL REFERENCES production_records(id),
                batch_id INTEGER NOT NULL REFERENCES material_batches(id),
                material_id INTEGER NOT NULL REFERENCES raw_materials(id),
                quantity REAL NOT NULL,
                created_at DATETIME
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS return_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                customer_id INTEGER REFERENCES customers(id),
                sales_order_id INTEGER REFERENCES sales_orders(id),
                product_id INTEGER NOT NULL REFERENCES products(id),
                quantity REAL NOT NULL,
                unit_price REAL,
                total_amount REAL,
                return_type TEXT NOT NULL,
                product_batch_ref TEXT,
                status TEXT DEFAULT '待处理',
                operator TEXT,
                notes TEXT,
                created_at DATETIME
            )
        """)
        print("新表创建: material_batches / batch_usages / return_records")

        # 2. 存量表加列
        for table, column, col_type in NEW_COLUMNS:
            cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
            if column not in cols:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
                print(f"加列: {table}.{column}")
            else:
                print(f"跳过（已存在）: {table}.{column}")

        # 3. 存量校验：原料/产品数应无损
        mat_count = conn.execute("SELECT COUNT(*) FROM raw_materials").fetchone()[0]
        prod_count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        print(f"存量校验: {mat_count} 原料 / {prod_count} 产品")

        conn.execute(f"PRAGMA user_version = {VERSION}")
        conn.commit()
        print(f"完成: user_version -> {VERSION}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()

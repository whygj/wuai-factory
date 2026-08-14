"""
v3.3 一次性迁移：BOM配方表 + 生产成本快照两列（user_version 5→6）

- 新表 boms（UNIQUE(product_id, material_id)，一个产品一份配方一料一行）
- production_records 加 material_cost REAL（可空）/ bom_snapshot TEXT（可空）

用法（backend/ 目录，先停服务）：
    sudo systemctl stop wuai-factory
    python3 migrate_v33.py
    sudo systemctl start wuai-factory
"""
import os
import shutil
import sqlite3
import sys
from datetime import datetime

DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "..", "data", "wuai.db"))

VERSION = 6


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
        if current_version < 5:
            print(f"user_version={current_version} < 5：请先执行 migrate_v32.py，再跑本脚本。")
            sys.exit(1)

        backup_dir = os.path.join(os.path.dirname(db_path), "..", "backups")
        os.makedirs(backup_dir, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"wuai_{stamp}.db")
        shutil.copy2(db_path, backup_path)
        print(f"已备份: {backup_path}")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS boms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL REFERENCES products(id),
                base_quantity REAL NOT NULL,
                base_unit TEXT NOT NULL,
                material_id INTEGER NOT NULL REFERENCES raw_materials(id),
                material_quantity REAL NOT NULL,
                material_unit TEXT NOT NULL,
                notes TEXT,
                created_at DATETIME,
                updated_at DATETIME
            )
        """)
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_bom_product_material ON boms(product_id, material_id)")
        print("新表创建: boms")

        cols = [r[1] for r in conn.execute("PRAGMA table_info(production_records)").fetchall()]
        if "material_cost" not in cols:
            conn.execute("ALTER TABLE production_records ADD COLUMN material_cost REAL")
            print("加列: production_records.material_cost")
        else:
            print("跳过（已存在）: production_records.material_cost")
        if "bom_snapshot" not in cols:
            conn.execute("ALTER TABLE production_records ADD COLUMN bom_snapshot TEXT")
            print("加列: production_records.bom_snapshot")
        else:
            print("跳过（已存在）: production_records.bom_snapshot")

        prod_count = conn.execute("SELECT COUNT(*) FROM production_records").fetchone()[0]
        mat_count = conn.execute("SELECT COUNT(*) FROM raw_materials").fetchone()[0]
        print(f"存量校验: {prod_count} 生产记录 / {mat_count} 原料")

        conn.execute(f"PRAGMA user_version = {VERSION}")
        conn.commit()
        print(f"完成: user_version -> {VERSION}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()

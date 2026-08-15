"""
v3.4 一次性迁移：领用记录台账表（user_version 6→7）

- 新表 usage_logs（领用台账，生产登记事务内自动写，只读不可改删）
- 零回填（线上零生产记录，与 v3.1 迁移策略一致）

用法（backend/ 目录，先停服务）：
    sudo systemctl stop wuai-factory
    python3 migrate_v34.py
    sudo systemctl start wuai-factory
"""
import os
import shutil
import sqlite3
import sys
from datetime import datetime

DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "..", "data", "wuai.db"))

VERSION = 7


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
        if current_version < 6:
            print(f"user_version={current_version} < 6：请先执行 migrate_v33.py，再跑本脚本。")
            sys.exit(1)

        backup_dir = os.path.join(os.path.dirname(db_path), "..", "backups")
        os.makedirs(backup_dir, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"wuai_{stamp}.db")
        shutil.copy2(db_path, backup_path)
        print(f"已备份: {backup_path}")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS usage_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                material_id INTEGER NOT NULL REFERENCES raw_materials(id),
                material_name TEXT NOT NULL,
                category TEXT,
                quantity REAL NOT NULL,
                unit TEXT,
                stock_after REAL,
                product_id INTEGER REFERENCES products(id),
                product_name TEXT,
                production_quantity REAL,
                production_id INTEGER REFERENCES production_records(id),
                source TEXT DEFAULT 'production',
                related_id INTEGER,
                operator TEXT,
                notes TEXT,
                created_at DATETIME
            )
        """)
        print("新表创建: usage_logs")

        prod_count = conn.execute("SELECT COUNT(*) FROM production_records").fetchone()[0]
        print(f"存量校验: {prod_count} 生产记录（零回填，台账从此刻起记）")

        conn.execute(f"PRAGMA user_version = {VERSION}")
        conn.commit()
        print(f"完成: user_version -> {VERSION}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()

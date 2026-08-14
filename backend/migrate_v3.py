"""
v3.0 一次性迁移：历史 created_at/updated_at 从 UTC 转为北京时间（+8小时）

背景：v2.x 所有 DateTime 默认值用 datetime.utcnow() 存储，界面显示差8小时。
v3.0 起代码统一写北京时间（backend/utils.py now_cn），本脚本把存量数据补齐。

用法（在 backend/ 目录下，先停服务）：
    sudo systemctl stop wuai-factory
    python3 migrate_v3.py          # 自动备份到 ../backups/ 后执行
    sudo systemctl start wuai-factory

幂等性：用 PRAGMA user_version=3 做标记，重复执行会直接跳过，不会二次+8h。
"""
import os
import shutil
import sqlite3
import sys
from datetime import datetime

DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "..", "data", "wuai.db"))

# 所有含 DateTime 时间戳列的表
TABLES = [
    "users", "raw_materials", "products", "inventory_transactions",
    "production_records", "shipment_records", "operation_logs",
    "customers", "suppliers", "sales_orders", "purchase_orders", "lab_records",
]

VERSION = 3


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

        # 备份
        backup_dir = os.path.join(os.path.dirname(db_path), "..", "backups")
        os.makedirs(backup_dir, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"wuai_{stamp}.db")
        shutil.copy2(db_path, backup_path)
        print(f"已备份: {backup_path}")

        total = 0
        for table in TABLES:
            cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
            time_cols = [c for c in ("created_at", "updated_at") if c in cols]
            for col in time_cols:
                cur = conn.execute(
                    f"UPDATE {table} SET {col} = datetime({col}, '+8 hours') WHERE {col} IS NOT NULL"
                )
                total += cur.rowcount
                print(f"  {table}.{col}: {cur.rowcount} 行")
        conn.execute(f"PRAGMA user_version = {VERSION}")
        conn.commit()
        print(f"完成：共更新 {total} 个时间戳，user_version -> {VERSION}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()

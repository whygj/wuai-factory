"""
v3.2 一次性迁移：供应商付款两列 + purchase_payments 流水表（user_version 4→5）

- purchase_orders 加 paid_amount REAL DEFAULT 0 / payment_status TEXT DEFAULT '未付款'
- 新表 purchase_payments（付款流水，只作废不物理删）
- return_records v3.1 已建（status 默认值从'待处理'改'有效'仅代码层默认，存量无数据零影响）

用法（backend/ 目录，先停服务）：
    sudo systemctl stop wuai-factory
    python3 migrate_v32.py
    sudo systemctl start wuai-factory
"""
import os
import shutil
import sqlite3
import sys
from datetime import datetime

DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "..", "data", "wuai.db"))

VERSION = 5


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
        if current_version < 4:
            print(f"user_version={current_version} < 4：请先执行 migrate_v31.py，再跑本脚本。")
            sys.exit(1)

        backup_dir = os.path.join(os.path.dirname(db_path), "..", "backups")
        os.makedirs(backup_dir, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"wuai_{stamp}.db")
        shutil.copy2(db_path, backup_path)
        print(f"已备份: {backup_path}")

        # 1. purchase_orders 加两列
        cols = [r[1] for r in conn.execute("PRAGMA table_info(purchase_orders)").fetchall()]
        if "paid_amount" not in cols:
            conn.execute("ALTER TABLE purchase_orders ADD COLUMN paid_amount REAL DEFAULT 0")
            print("加列: purchase_orders.paid_amount")
        else:
            print("跳过（已存在）: purchase_orders.paid_amount")
        if "payment_status" not in cols:
            conn.execute("ALTER TABLE purchase_orders ADD COLUMN payment_status TEXT DEFAULT '未付款'")
            print("加列: purchase_orders.payment_status")
        else:
            print("跳过（已存在）: purchase_orders.payment_status")

        # 2. 新表
        conn.execute("""
            CREATE TABLE IF NOT EXISTS purchase_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                purchase_order_id INTEGER NOT NULL REFERENCES purchase_orders(id),
                amount REAL NOT NULL,
                date DATE NOT NULL,
                method TEXT,
                status TEXT DEFAULT '有效',
                operator TEXT,
                notes TEXT,
                created_at DATETIME
            )
        """)
        print("新表创建: purchase_payments")

        # 3. 存量校验
        po_count = conn.execute("SELECT COUNT(*) FROM purchase_orders").fetchone()[0]
        zero_paid = conn.execute("SELECT COUNT(*) FROM purchase_orders WHERE paid_amount = 0 OR paid_amount IS NULL").fetchone()[0]
        unpaid = conn.execute("SELECT COUNT(*) FROM purchase_orders WHERE payment_status = '未付款'").fetchone()[0]
        print(f"存量校验: {po_count} 采购单，{zero_paid} 已付=0，{unpaid} 状态=未付款")

        conn.execute(f"PRAGMA user_version = {VERSION}")
        conn.commit()
        print(f"完成: user_version -> {VERSION}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()

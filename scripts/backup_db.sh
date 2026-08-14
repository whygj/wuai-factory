#!/bin/bash
# 五爱工厂数据库每日备份（crontab 示例：30 2 * * * /home/ubuntu/projects/active/wuai-factory/scripts/backup_db.sh）
# sqlite3 .backup 是在线安全备份，不需要停服务；保留最近30天

DB_PATH="${DB_PATH:-/home/ubuntu/projects/active/wuai-factory/data/wuai.db}"
BACKUP_DIR="${BACKUP_DIR:-/home/ubuntu/projects/active/wuai-factory/backups}"
KEEP_DAYS=30

mkdir -p "$BACKUP_DIR"
STAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/wuai_$STAMP.db"

if [ ! -f "$DB_PATH" ]; then
  echo "[backup] 数据库不存在: $DB_PATH"
  exit 1
fi

sqlite3 "$DB_PATH" ".backup '$BACKUP_FILE'"
if [ $? -eq 0 ] && [ -s "$BACKUP_FILE" ]; then
  gzip -f "$BACKUP_FILE"
  echo "[backup] OK: ${BACKUP_FILE}.gz ($(du -h ${BACKUP_FILE}.gz | cut -f1))"
else
  echo "[backup] FAILED"
  exit 1
fi

# 清理过期备份
find "$BACKUP_DIR" -name "wuai_*.db.gz" -mtime +$KEEP_DAYS -delete
find "$BACKUP_DIR" -name "wuai_*.db" -mtime +$KEEP_DAYS -delete
echo "[backup] 清理 ${KEEP_DAYS} 天前的旧备份完成"

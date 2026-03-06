"""
数据库迁移脚本：为现有表添加 asset_type 字段
由于 SQLite 不直接支持 ALTER TABLE ADD COLUMN IF NOT EXISTS，
我们需要手动处理。
"""
import sqlite3
from pathlib import Path

db_path = Path(__file__).parent / "quant_trader.db"

if not db_path.exists():
    print("Database not found, nothing to migrate")
    exit(0)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 检查 watchlist 表是否已有 asset_type 列
cursor.execute("PRAGMA table_info(watchlist)")
columns = [col[1] for col in cursor.fetchall()]

if 'asset_type' not in columns:
    print("Adding asset_type to watchlist...")
    cursor.execute("ALTER TABLE watchlist ADD COLUMN asset_type TEXT DEFAULT 'stock'")
    print("Done")
else:
    print("watchlist.asset_type already exists")

# 检查 signals 表
cursor.execute("PRAGMA table_info(signals)")
columns = [col[1] for col in cursor.fetchall()]

if 'asset_type' not in columns:
    print("Adding asset_type to signals...")
    cursor.execute("ALTER TABLE signals ADD COLUMN asset_type TEXT DEFAULT 'stock'")
    print("Done")
else:
    print("signals.asset_type already exists")

# 检查 backtests 表
cursor.execute("PRAGMA table_info(backtests)")
columns = [col[1] for col in cursor.fetchall()]

if 'asset_type' not in columns:
    print("Adding asset_type to backtests...")
    cursor.execute("ALTER TABLE backtests ADD COLUMN asset_type TEXT DEFAULT 'stock'")
    print("Done")
else:
    print("backtests.asset_type already exists")

conn.commit()
conn.close()
print("Migration complete!")

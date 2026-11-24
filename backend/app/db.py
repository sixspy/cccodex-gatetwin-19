import os
import sqlite3
from pathlib import Path

数据目录 = Path(os.environ.get("数据目录", Path(__file__).resolve().parent.parent / "data"))
夹具目录 = Path(os.environ.get("夹具目录", Path(__file__).resolve().parent.parent.parent / "fixtures"))
库路径 = 数据目录 / "闸对.db"


def 连接(隔离: str | None = "") -> sqlite3.Connection:
    """打开数据库连接。

    隔离=""  → sqlite3 默认（隐式事务，兼容原主链路）
    隔离=None → 自动提交，由调用方显式 BEGIN IMMEDIATE / COMMIT 控制写闸事务
    """
    数据目录.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(库路径, timeout=30)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    if 隔离 is None:
        c.isolation_level = None
    return c

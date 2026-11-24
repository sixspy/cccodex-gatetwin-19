import sqlite3
from datetime import datetime, timezone

from app.db import 连接

建表 = """
CREATE TABLE IF NOT EXISTS 站规 (
  键 TEXT PRIMARY KEY,
  值 TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS 线路 (
  线路键 TEXT PRIMARY KEY,
  名称 TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS 站点 (
  站点键 TEXT PRIMARY KEY,
  线路键 TEXT NOT NULL REFERENCES 线路(线路键),
  站名 TEXT NOT NULL,
  站序 INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS 刷卡点 (
  事件编号 TEXT PRIMARY KEY,
  卡号 TEXT NOT NULL,
  站点键 TEXT NOT NULL,
  方向 TEXT NOT NULL,
  事件时 TEXT NOT NULL,
  处理时 TEXT NOT NULL,
  命运 TEXT NOT NULL DEFAULT '已入流',
  行程键 TEXT NOT NULL DEFAULT '',
  批次编号 TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS 装载批次 (
  编号 TEXT PRIMARY KEY,
  时刻 TEXT NOT NULL,
  报告 TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS 开腿账 (
  开腿键 TEXT PRIMARY KEY,
  卡号 TEXT NOT NULL,
  进站事件编号 TEXT NOT NULL,
  进站站点键 TEXT NOT NULL,
  进站事件时 TEXT NOT NULL,
  状态 TEXT NOT NULL DEFAULT '在途',
  更新处理时 TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS 行程账 (
  行程键 TEXT PRIMARY KEY,
  卡号 TEXT NOT NULL,
  进站事件编号 TEXT NOT NULL,
  出站事件编号 TEXT NOT NULL,
  进站站点键 TEXT NOT NULL,
  出站站点键 TEXT NOT NULL,
  进站事件时 TEXT NOT NULL,
  出站事件时 TEXT NOT NULL,
  历时秒 INTEGER NOT NULL DEFAULT 0,
  状态 TEXT NOT NULL DEFAULT '已成对',
  版本 INTEGER NOT NULL DEFAULT 1,
  处理时 TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS 旁路匣 (
  编号 INTEGER PRIMARY KEY AUTOINCREMENT,
  原因 TEXT NOT NULL,
  卡号 TEXT NOT NULL DEFAULT '',
  事件编号 TEXT NOT NULL DEFAULT '',
  载荷 TEXT NOT NULL,
  时刻 TEXT NOT NULL,
  状态 TEXT NOT NULL DEFAULT '开'
);
CREATE TABLE IF NOT EXISTS 补录闸 (
  编号 INTEGER PRIMARY KEY AUTOINCREMENT,
  闸态 TEXT NOT NULL,
  原因 TEXT NOT NULL DEFAULT '',
  时刻 TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS 补录账 (
  编号 INTEGER PRIMARY KEY AUTOINCREMENT,
  时刻 TEXT NOT NULL,
  请求编号 TEXT NOT NULL DEFAULT '',
  闸态 TEXT NOT NULL,
  旁路编号 INTEGER NOT NULL DEFAULT 0,
  卡号 TEXT NOT NULL DEFAULT '',
  出站事件编号 TEXT NOT NULL DEFAULT '',
  补录站点键 TEXT NOT NULL DEFAULT '',
  虚进事件编号 TEXT NOT NULL DEFAULT '',
  开腿键 TEXT NOT NULL DEFAULT '',
  行程键 TEXT NOT NULL DEFAULT '',
  结果 TEXT NOT NULL,
  拒绝原因 TEXT NOT NULL DEFAULT '',
  审计口径 TEXT NOT NULL DEFAULT 'manual_stop',
  载荷 TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS 行程贯验 (
  编号 INTEGER PRIMARY KEY AUTOINCREMENT,
  时刻 TEXT NOT NULL,
  刷卡数 INTEGER NOT NULL,
  行程数 INTEGER NOT NULL,
  开腿数 INTEGER NOT NULL,
  旁路数 INTEGER NOT NULL,
  是否通过 INTEGER NOT NULL,
  说明 TEXT NOT NULL
);
"""


def 此刻() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _补列(conn, 表: str, 列: str, 定义: str) -> None:
    """给既有库补列（CREATE TABLE IF NOT EXISTS 不会改老表）。"""
    try:
        现有 = {r["name"] for r in conn.execute(f"PRAGMA table_info({表})")}
    except sqlite3.Error:
        return
    if 列 not in 现有:
        conn.execute(f"ALTER TABLE {表} ADD COLUMN {列} {定义}")


def _迁移升级(conn) -> None:
    _补列(conn, "旁路匣", "状态", "TEXT NOT NULL DEFAULT '开'")
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS 补录账_已补录_请求号 "
        "ON 补录账(请求编号) WHERE 结果='已成对' AND 请求编号<>''"
    )


def 初始化库() -> None:
    conn = 连接()
    conn.executescript(建表)
    _迁移升级(conn)
    if conn.execute("SELECT COUNT(*) AS c FROM 站规").fetchone()["c"] == 0:
        for k, v in {
            "站名": "闸对",
            "最大行程秒": "7200",
            "同站进出": "允许",
            "重复进站策略": "旧腿旁路并开新腿",
            "配对策略": "同卡先进后出",
            "骨架": "刷卡点装载→同卡进站出站成对物化→缺腿异向超时旁路→行程账与刷卡点互证",
        }.items():
            conn.execute("INSERT INTO 站规(键, 值) VALUES (?, ?)", (k, v))
    if conn.execute("SELECT COUNT(*) AS c FROM 线路").fetchone()["c"] == 0:
        conn.execute("INSERT INTO 线路(线路键, 名称) VALUES (?, ?)", ("线1", "一号线"))
        for i, (k, n) in enumerate(
            [("站A", "城东站"), ("站B", "中心站"), ("站C", "河西站")], start=1
        ):
            conn.execute(
                "INSERT INTO 站点(站点键, 线路键, 站名, 站序) VALUES (?,?,?,?)",
                (k, "线1", n, i),
            )
    if conn.execute("SELECT COUNT(*) AS c FROM 补录闸").fetchone()["c"] == 0:
        conn.execute(
            "INSERT INTO 补录闸(闸态, 原因, 时刻) VALUES ('关', '默认闸关', ?)", (此刻(),)
        )
    if not conn.execute("SELECT 1 FROM 站规 WHERE 键='补录口径'").fetchone():
        conn.execute(
            "INSERT INTO 站规(键, 值) VALUES (?, ?)",
            ("补录口径", "manual_stop：须请求体指定补录进站站且权威可解，缺参/未知站拒绝，禁止自动首站"),
        )
    conn.commit()
    conn.close()

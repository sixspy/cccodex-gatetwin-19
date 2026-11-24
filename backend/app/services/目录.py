from app.db import 连接


def 总览() -> dict:
    conn = 连接()
    try:
        def c(sql: str) -> int:
            return conn.execute(sql).fetchone()[0]

        末 = conn.execute(
            "SELECT * FROM 行程贯验 ORDER BY 编号 DESC LIMIT 1"
        ).fetchone()
        return {
            "站点": c("SELECT COUNT(*) FROM 站点"),
            "刷卡点": c("SELECT COUNT(*) FROM 刷卡点"),
            "已开腿": c("SELECT COUNT(*) FROM 刷卡点 WHERE 命运='已开腿'"),
            "已成对": c("SELECT COUNT(*) FROM 刷卡点 WHERE 命运='已成对'"),
            "已旁路": c("SELECT COUNT(*) FROM 刷卡点 WHERE 命运='已旁路'"),
            "在途开腿": c("SELECT COUNT(*) FROM 开腿账 WHERE 状态='在途'"),
            "行程数": c("SELECT COUNT(*) FROM 行程账 WHERE 状态='已成对'"),
            "旁路匣": c("SELECT COUNT(*) FROM 旁路匣"),
            "装载批次": c("SELECT COUNT(*) FROM 装载批次"),
            "末次贯验": dict(末) if 末 else None,
        }
    finally:
        conn.close()

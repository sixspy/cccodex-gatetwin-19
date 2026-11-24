"""出站无进补录闸。

已旁路的「出站孤儿」若要补录成行程，必须经本闸。

架构口径（全局唯一，关键词 ``manual_stop``）：**以请求体指定补录站为准**。
- 必须传补录站点键，且该站点须在「站点」权威表可解；
- 缺参 / 未知站一律拒绝，不做线路首站兜底（禁止自动首站）；
- 审计口径固定记 ``manual_stop``。

写闸硬约束：
- 闸开/闸关与虚进写入**同成败**：闸关时不得写虚进，闸开时才可能写；
- 一切写入在单个 ``BEGIN IMMEDIATE`` 事务内完成，失败整体回滚；
- 禁止绕过旁路终态直接把已成对改写：必须先有「出站孤儿」旁路记录，
  再经本闸插入虚进刷卡点与开腿账、调用配对物化行程，并同步把旁路关闭；
- 「结果与旁路关闭同票」：行程落账与旁路状态置 ``已补录`` 在同一事务提交；
- 并发补录同一旁路：``BEGIN IMMEDIATE`` + 补录账部分唯一索引双保险，绝不双落。
"""

import json

from app.db import 连接
from app.seed import 此刻
from app.services import 配对

NAME = "出站无进补录闸"

口径 = "manual_stop"
闸开 = "开"
闸关 = "关"

旁路原因出站孤儿 = "出站孤儿"
旁路状态开 = "开"
旁路状态已补录 = "已补录"


def _闸态(conn) -> str:
    行 = conn.execute("SELECT 闸态 FROM 补录闸 ORDER BY 编号 DESC LIMIT 1").fetchone()
    return 行["闸态"] if 行 else 闸关


def 读闸(conn) -> dict:
    return {"闸开关": _闸态(conn), "口径": 口径}


def 开关闸(闸态: str, 原因: str = "") -> dict:
    闸态 = (闸态 or "").strip()
    if 闸态 not in (闸开, 闸关):
        return {"ok": False, "拒绝": "闸态非法，只接受 开/关"}
    conn = 连接(隔离=None)
    try:
        conn.execute("BEGIN IMMEDIATE")
        处理时 = 此刻()
        conn.execute(
            "INSERT INTO 补录闸(闸态, 原因, 时刻) VALUES (?,?,?)",
            (闸态, 原因 or "", 处理时),
        )
        conn.commit()
        return {"ok": True, "闸开关": 闸态, "口径": 口径, "时刻": 处理时}
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _取旁路(conn, 旁路编号: int | None, 出站事件编号: str) -> dict:
    """按编号或出站事件编号定位一条旁路；返回校验结果。"""
    行 = None
    if 旁路编号:
        行 = conn.execute("SELECT * FROM 旁路匣 WHERE 编号=?", (旁路编号,)).fetchone()
    elif 出站事件编号:
        行 = conn.execute(
            """SELECT * FROM 旁路匣
               WHERE 事件编号=? AND 原因=?
               ORDER BY 编号 DESC LIMIT 1""",
            (出站事件编号, 旁路原因出站孤儿),
        ).fetchone()
    if not 行:
        return {"ok": False, "拒绝": "旁路不存在", "旁路": None}
    if 行["原因"] != 旁路原因出站孤儿:
        return {"ok": False, "拒绝": f"旁路原因非出站孤儿（{行['原因']}）", "旁路": dict(行)}
    if 行["状态"] != 旁路状态开:
        return {"ok": False, "拒绝": f"旁路已关闭（{行['状态']}）", "旁路": dict(行)}

    出站 = conn.execute("SELECT * FROM 刷卡点 WHERE 事件编号=?", (行["事件编号"],)).fetchone()
    if not 出站:
        return {"ok": False, "拒绝": "旁路对应出站刷卡点缺失", "旁路": dict(行)}
    if 出站["方向"] != "出站":
        return {"ok": False, "拒绝": "旁路对应事件方向非出站", "旁路": dict(行)}
    if 出站["命运"] != "已旁路":
        return {"ok": False, "拒绝": f"出站刷卡命运非已旁路（{出站['命运']}）", "旁路": dict(行)}
    if 出站["卡号"] != 行["卡号"]:
        return {"ok": False, "拒绝": "旁路卡号与出站刷卡不一致", "旁路": dict(行)}
    return {"ok": True, "旁路": dict(行), "出站": dict(出站)}


def 预演(conn, 旁路编号: int | None = None, 出站事件编号: str = "", 补录站点键: str = "") -> dict:
    """只读推演：不写任何数据，给出「若此刻补录」的判定与虚进站/行程。"""
    结果 = {
        "闸开关": _闸态(conn),
        "口径": 口径,
        "旁路编号": 旁路编号 or None,
        "旁路原因": "",
        "旁路状态": "",
        "卡号": "",
        "补录站点键": (补录站点键 or "").strip(),
        "虚进站": "",
        "行程": None,
        "拒绝": "",
        "valid": False,
    }
    取 = _取旁路(conn, 旁路编号, 出站事件编号)
    if 取.get("旁路"):
        结果["旁路编号"] = 取["旁路"]["编号"]
        结果["旁路原因"] = 取["旁路"]["原因"]
        结果["旁路状态"] = 取["旁路"]["状态"]
        结果["卡号"] = 取["旁路"]["卡号"]
        结果["出站事件编号"] = 取["旁路"]["事件编号"]
    if not 取["ok"]:
        结果["拒绝"] = 取["拒绝"]
        return 结果
    if 结果["闸开关"] != 闸开:
        结果["拒绝"] = "补录闸未开"
        return 结果

    站键 = 结果["补录站点键"]
    if not 站键:
        结果["拒绝"] = "缺补录站点键"
        return 结果
    站行 = conn.execute("SELECT * FROM 站点 WHERE 站点键=?", (站键,)).fetchone()
    if not 站行:
        结果["拒绝"] = f"补录站点未知:{站键}"
        return 结果

    旁路 = 取["旁路"]
    出站 = 取["出站"]
    虚进编号 = f"虚进-{旁路['编号']}"
    if conn.execute("SELECT 1 FROM 刷卡点 WHERE 事件编号=?", (虚进编号,)).fetchone():
        结果["拒绝"] = f"虚进事件编号冲突:{虚进编号}"
        return 结果
    结果["虚进站"] = 站键
    结果["valid"] = True
    结果["虚进事件编号"] = 虚进编号
    结果["行程"] = {
        "行程键": f"行-{虚进编号}-{出站['事件编号']}",
        "卡号": 旁路["卡号"],
        "进站事件编号": 虚进编号,
        "进站站点键": 站键,
        "出站事件编号": 出站["事件编号"],
        "出站站点键": 出站["站点键"],
        "进站事件时": 出站["事件时"],
        "出站事件时": 出站["事件时"],
        "历时秒": 0,
        "状态": "已成对",
    }
    return 结果


def 补录(体: dict) -> dict:
    """经闸补录：单事务内写虚进 → 开腿 → 成对 → 关旁路 → 记审计。"""
    请求编号 = (体.get("请求编号") or "").strip()
    旁路编号 = 体.get("旁路编号")
    try:
        旁路编号 = int(旁路编号) if 旁路编号 not in (None, "", 0) else None
    except (TypeError, ValueError):
        旁路编号 = None
    出站事件编号 = (体.get("出站事件编号") or "").strip()
    补录站点键 = (体.get("补录站点键") or "").strip()
    处理时 = 此刻()

    conn = 连接(隔离=None)
    try:
        conn.execute("BEGIN IMMEDIATE")

        # 请求编号幂等：同号已成对过则原样返回，不重复写（被拒的不算，可修正后重试）
        if 请求编号:
            旧 = conn.execute(
                "SELECT * FROM 补录账 WHERE 请求编号=? AND 结果='已成对' ORDER BY 编号 DESC LIMIT 1",
                (请求编号,),
            ).fetchone()
            if 旧:
                conn.rollback()
                return _账转结果(旧) | {"ok": True, "幂等": True}

        预 = 预演(
            conn,
            旁路编号=旁路编号,
            出站事件编号=出站事件编号,
            补录站点键=补录站点键,
        )
        if not 预["valid"]:
            账 = _记审计(conn, 请求编号, 预, 结果="拒绝", 拒绝原因=预["拒绝"], 时刻=处理时)
            conn.commit()
            return _账转结果(账) | {"ok": False}

        旁路编号 = 预["旁路编号"]
        旁路 = conn.execute("SELECT * FROM 旁路匣 WHERE 编号=?", (旁路编号,)).fetchone()
        出站 = conn.execute("SELECT * FROM 刷卡点 WHERE 事件编号=?", (旁路["事件编号"],)).fetchone()
        虚进编号 = 预["虚进事件编号"]

        # 虚进刷卡点（进站）
        conn.execute(
            """INSERT INTO 刷卡点(事件编号,卡号,站点键,方向,事件时,处理时,命运,行程键,批次编号)
               VALUES (?,?,?,?,?,?, '已开腿', '', '补录闸')""",
            (
                虚进编号,
                旁路["卡号"],
                预["补录站点键"],
                "进站",
                出站["事件时"],
                处理时,
            ),
        )
        # 虚进开腿
        开腿键 = f"腿-{虚进编号}"
        conn.execute(
            """INSERT INTO 开腿账(开腿键,卡号,进站事件编号,进站站点键,进站事件时,状态,更新处理时)
               VALUES (?,?,?,?,?, '在途', ?)""",
            (
                开腿键,
                旁路["卡号"],
                虚进编号,
                预["补录站点键"],
                出站["事件时"],
                处理时,
            ),
        )
        # 成对物化：进=虚进，出=原孤儿出站；同时把两笔刷卡置已成对
        开腿 = {
            "开腿键": 开腿键,
            "卡号": 旁路["卡号"],
            "进站事件编号": 虚进编号,
            "进站站点键": 预["补录站点键"],
            "进站事件时": 出站["事件时"],
        }
        行程键 = 配对.成对写出站(
            conn, 开腿, 出站["事件编号"], 出站["站点键"], 出站["事件时"], 处理时
        )
        # 结果与旁路关闭同票
        conn.execute(
            "UPDATE 旁路匣 SET 状态=? WHERE 编号=?",
            (旁路状态已补录, 旁路编号),
        )
        账 = _记审计(
            conn,
            请求编号,
            预,
            结果="已成对",
            拒绝原因="",
            时刻=处理时,
            虚进事件编号=虚进编号,
            开腿键=开腿键,
            行程键=行程键,
            载荷={
                "补录站点键": 预["补录站点键"],
                "线路键": _站线路(conn, 预["补录站点键"]),
                "旁路编号": 旁路编号,
                "出站事件编号": 出站["事件编号"],
                "审计": 口径,
            },
        )
        conn.commit()
        return _账转结果(账) | {"ok": True}
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _站线路(conn, 站点键: str) -> str:
    行 = conn.execute("SELECT 线路键 FROM 站点 WHERE 站点键=?", (站点键,)).fetchone()
    return 行["线路键"] if 行 else ""


def _记审计(
    conn,
    请求编号: str,
    预: dict,
    结果: str,
    拒绝原因: str,
    时刻: str,
    虚进事件编号: str = "",
    开腿键: str = "",
    行程键: str = "",
    载荷: dict | None = None,
) -> dict:
    cur = conn.execute(
        """INSERT INTO 补录账(时刻,请求编号,闸态,旁路编号,卡号,出站事件编号,补录站点键,
           虚进事件编号,开腿键,行程键,结果,拒绝原因,审计口径,载荷)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            时刻,
            请求编号,
            预.get("闸开关", 闸关),
            int(预.get("旁路编号") or 0),
            预.get("卡号", ""),
            预.get("出站事件编号", ""),
            预.get("补录站点键", ""),
            虚进事件编号,
            开腿键,
            行程键,
            结果,
            拒绝原因,
            口径,
            json.dumps(载荷 or {}, ensure_ascii=False),
        ),
    )
    return dict(
        conn.execute("SELECT * FROM 补录账 WHERE 编号=?", (cur.lastrowid,)).fetchone()
    )


def _账转结果(账) -> dict:
    if not isinstance(账, dict):
        账 = dict(账)
    out = dict(账)
    try:
        out["载荷"] = json.loads(out.get("载荷") or "{}")
    except Exception:
        pass
    out["虚进站"] = 账.get("补录站点键", "") if 账.get("结果") == "已成对" else ""
    out["闸开关"] = 账.get("闸态", 闸关)
    out["口径"] = 账.get("审计口径", 口径)
    out["行程"] = (
        {"行程键": 账.get("行程键", ""), "卡号": 账.get("卡号", "")}
        if 账.get("行程键")
        else None
    )
    out["拒绝"] = 账.get("拒绝原因", "") if 账.get("结果") != "已成对" else ""
    out["valid"] = 账.get("结果") == "已成对"
    return out


def 列补录账(限: int = 100) -> list[dict]:
    conn = 连接()
    try:
        行 = [dict(r) for r in conn.execute("SELECT * FROM 补录账 ORDER BY 编号 DESC LIMIT ?", (限,))]
        for r in 行:
            try:
                r["载荷"] = json.loads(r.get("载荷") or "{}")
            except Exception:
                pass
        return 行
    finally:
        conn.close()

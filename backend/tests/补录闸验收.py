"""出站无进补录闸 · 验收脚本（不依赖 HTTP，直接调用服务层）。

用法（仓库根目录）：
    .venv/bin/python backend/tests/补录闸验收.py

覆盖夹具：
  1) 孤儿旁路后闸开不带站补录 → 拒绝（缺补录站点键）
  2) 孤儿旁路后闸开带合法站 → 成对，虚进=指定站，审计 manual_stop
  3) 闸关 → 拒绝（补录闸未开）
  4) 补录与旁路并发 → 不得双落（仅一笔行程，旁路同票关闭）
"""

import os
import sys
import tempfile
import threading
from pathlib import Path

根 = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(根))

os.environ["数据目录"] = tempfile.mkdtemp(prefix="补录闸验收-")
os.environ["夹具目录"] = str(根.parent / "fixtures")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

通过 = 0
失败 = 0


def 验(名: str, 条件: bool, 备注: str = "") -> None:
    global 通过, 失败
    if 条件:
        通过 += 1
        print(f"  ✔ {名}")
    else:
        失败 += 1
        print(f"  ✘ {名} {备注}")


def 主() -> int:
    with TestClient(app) as c:
        孤儿 = {"事件编号": "o1", "卡号": "卡77", "站点键": "站C",
                "方向": "出站", "事件时": "2026-11-22T10:00:00Z"}
        c.post("/api/装载", json={"批次编号": "批-验收孤儿", "事件": [孤儿]})
        print("【前置】孤儿出站已进旁路：",
              c.get("/api/旁路匣").json()[0]["原因"])

        print("\n【1】闸关补录 → 拒绝")
        r = c.post("/api/补录闸/补录", json={"出站事件编号": "o1", "补录站点键": "站B"})
        验("HTTP 409", r.status_code == 409, r.text)
        验("拒绝=补录闸未开", r.json()["detail"]["拒绝"] == "补录闸未开", r.text)
        验("未成对", c.get("/api/行程账").json() == [])

        print("\n【2】闸开不带站补录 → 拒绝（manual_stop 禁自动首站）")
        c.post("/api/补录闸/开关", json={"闸态": "开"})
        r = c.post("/api/补录闸/补录", json={"出站事件编号": "o1"})
        验("HTTP 409", r.status_code == 409, r.text)
        验("拒绝=缺补录站点键", r.json()["detail"]["拒绝"] == "缺补录站点键", r.text)
        验("验无行程", c.get("/api/行程账").json() == [])

        print("\n【3】闸开未知站补录 → 拒绝")
        r = c.post("/api/补录闸/补录", json={"出站事件编号": "o1", "补录站点键": "站X"})
        验("HTTP 409", r.status_code == 409, r.text)
        验("拒绝含未知", "未知" in r.json()["detail"]["拒绝"], r.text)

        print("\n【4】闸开带合法站补录 → 成对，虚进=指定站")
        r = c.post("/api/补录闸/补录",
                   json={"出站事件编号": "o1", "补录站点键": "站B", "请求编号": "q1"})
        j = r.json()
        验("HTTP 200", r.status_code == 200, r.text)
        验("结果=已成对", j.get("结果") == "已成对", r.text)
        验("虚进站=站B", j.get("虚进站") == "站B", r.text)
        验("审计=manual_stop", j.get("审计口径") == "manual_stop", r.text)
        行程 = c.get("/api/行程账").json()
        验("行程进站=站B", len(行程) == 1 and 行程[0]["进站站点键"] == "站B", str(行程))
        旁 = c.get("/api/旁路匣").json()
        验("旁路同票关闭=已补录", 旁[0]["状态"] == "已补录", str(旁))

        print("\n【5】重复补录（同请求号）→ 幂等，不双落")
        r = c.post("/api/补录闸/补录",
                   json={"出站事件编号": "o1", "补录站点键": "站B", "请求编号": "q1"})
        验("HTTP 200", r.status_code == 200, r.text)
        验("幂等=true", r.json().get("幂等") is True, r.text)
        验("行程仍为 1 笔", len(c.get("/api/行程账").json()) == 1)

        print("\n【6】再造孤儿旁路 + 并发补录 → 不得双落")
        c.post("/api/装载", json={"批次编号": "批-验收并发",
                                  "事件": [dict(孤儿, 事件编号="o2", 卡号="卡78",
                                               事件时="2026-11-22T11:00:00Z")]})
        结果 = []

        def 冲(站键: str) -> None:
            rr = c.post("/api/补录闸/补录", json={"出站事件编号": "o2", "补录站点键": 站键})
            结果.append((站键, rr.status_code))

        ts = [threading.Thread(target=冲, args=("站A",)),
              threading.Thread(target=冲, args=("站B",))]
        [t.start() for t in ts]
        [t.join() for t in ts]
        成功 = [x for x in 结果 if x[1] == 200]
        验("仅一方成功", len(成功) == 1, str(结果))
        验("o2 行程恰 1 笔",
           len([t for t in c.get("/api/行程账").json() if t["出站事件编号"] == "o2"]) == 1)

        print("\n【7】补录与旁路装载并发（同源再投递）→ 不得双落")
        c.post("/api/装载", json={"批次编号": "批-验收复投",
                                  "事件": [dict(孤儿, 事件编号="o3", 卡号="卡79",
                                               事件时="2026-11-22T13:00:00Z")]})
        混合 = []

        def 补() -> None:
            rr = c.post("/api/补录闸/补录", json={"出站事件编号": "o3", "补录站点键": "站B"})
            混合.append(("补录", rr.status_code))

        def 复投() -> None:
            rr = c.post("/api/装载", json={"批次编号": "批-验收复投2",
                                          "事件": [dict(孤儿, 事件编号="o3", 卡号="卡79",
                                                       事件时="2026-11-22T13:00:00Z")]})
            混合.append(("复投", rr.status_code))

        ts = [threading.Thread(target=补), threading.Thread(target=复投)]
        [t.start() for t in ts]
        [t.join() for t in ts]
        o3 = [t for t in c.get("/api/行程账").json() if t["出站事件编号"] == "o3"]
        验("o3 行程恰 1 笔", len(o3) == 1, str(混合))
        虚进 = {t["进站事件编号"] for t in o3}
        验("o3 恰 1 个虚进", len(虚进) == 1, str(o3))
        验("o3 补录成对审计恰 1 条",
           len([a for a in c.get("/api/补录账").json()
                if a["出站事件编号"] == "o3" and a["结果"] == "已成对"]) == 1)

        print("\n【8】贯验对齐")
        v = c.post("/api/贯验").json()
        验("行程贯验通过", v["是否通过"] is True, v["说明"])

    print(f"\n通过 {通过} · 失败 {失败}")
    return 0 if 失败 == 0 else 1


if __name__ == "__main__":
    raise SystemExit(主())

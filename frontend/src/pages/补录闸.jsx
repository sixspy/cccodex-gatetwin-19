import React, { useEffect, useMemo, useState } from "react";
import { 取, 递 } from "../api.js";

// 与后端 calls 保持一致：只读预演 + 经闸补录 + 开关闸。
async function 预演(参) {
  const q = new URLSearchParams();
  if (参.旁路编号) q.set("旁路编号", 参.旁路编号);
  if (参.出站事件编号) q.set("出站事件编号", 参.出站事件编号);
  if (参.补录站点键) q.set("补录站点键", 参.补录站点键);
  return 取(`/补录闸/预演?${q.toString()}`);
}

export default function 补录闸() {
  const [闸, 设闸] = useState(null);
  const [旁路, 设旁路] = useState([]);
  const [站, 设站] = useState([]);
  const [选旁路, 设选旁路] = useState("");
  const [站键, 设站键] = useState("");
  const [预, 设预] = useState(null);
  const [讯, 设讯] = useState("");
  const [账, 设账] = useState([]);
  const [请求号, 设请求号] = useState("");

  const 刷闸 = () => 取("/补录闸").then(设闸);
  const 刷账 = () => 取("/补录账").then(设账);
  const 刷旁路 = () =>
    取("/旁路匣").then((行) => 设旁路(行.filter((r) => r.原因 === "出站孤儿")));
  const 刷站 = () =>
    取("/线路").then((线) =>
      设站(线.flatMap((ln) => (ln.站点 || []).map((s) => ({ ...s, 线路键: ln.线路键 }))))
    );

  useEffect(() => {
    刷闸();
    刷旁路();
    刷站();
    刷账();
  }, []);

  const 当前旁路 = useMemo(
    () => 旁路.find((r) => String(r.编号) === String(选旁路)),
    [旁路, 选旁路]
  );

  useEffect(() => {
    if (!选旁路) {
      设预(null);
      return;
    }
    预演({ 旁路编号: 选旁路, 补录站点键: 站键 })
      .then(设预)
      .catch(() => 设预(null));
  }, [选旁路, 站键]);

  const 切闸 = async (目标) => {
    设讯("");
    try {
      await 递("/补录闸/开关", { 闸态: 目标, 原因: "运营台切换" });
      await 刷闸();
      设讯(`补录闸已${目标 === "开" ? "开" : "关"}`);
    } catch (e) {
      设讯(String(e.message || e));
    }
  };

  const 补录 = async () => {
    设讯("");
    try {
      const r = await 递("/补录闸/补录", {
        请求编号: 请求号.trim(),
        旁路编号: 选旁路 ? Number(选旁路) : null,
        补录站点键: 站键,
      });
      设讯(`已成对：虚进 ${r.虚进站} → 行程 ${r.行程键}（审计 ${r.审计口径}）`);
      await Promise.all([刷旁路(), 刷账(), 刷闸()]);
    } catch (e) {
      // 409 时后端带出拒绝明细
      let 拒 = String(e.message || e);
      try {
        const j = JSON.parse(拒);
        拒 = j.detail?.拒绝 || 拒;
      } catch {}
      设讯(`拒绝：${拒}`);
    }
  };

  const 开 = 闸?.闸开关 === "开";

  return (
    <div>
      <h1 className="题">补录闸</h1>
      <p className="述">
        出站孤儿旁路终态只可经本闸补录成行程：<strong>闸开/关与虚进写入同成败</strong>。口径{" "}
        <code>manual_stop</code> —— 必须指定补录进站站且须在站点权威表可解，缺参/未知站一律拒绝，禁止自动首站。
      </p>

      <div className="行" style={{ gap: "0.7rem" }}>
        <span>当前闸</span>
        <span className={`徽章 ${开 ? "通" : "败"}`}>{开 ? "开" : "关"}</span>
        <span className="讯" style={{ margin: 0 }}>口径 {闸?.口径 || "—"}</span>
        <button className="次" onClick={() => 切闸("开")} disabled={开}>开闸</button>
        <button className="次" onClick={() => 切闸("关")} disabled={!开}>关闸</button>
        <button className="次" onClick={刷闸}>刷新</button>
      </div>

      {讯 && <p className="讯">{讯}</p>}

      {!旁路.length ? (
        <div className="空态">暂无「出站孤儿」旁路。先在刷卡流灌「出站孤儿样例」。</div>
      ) : (
        <div className="段">
          <div className="段题">待补录旁路（出站孤儿）</div>
          <table>
            <thead>
              <tr><th>#</th><th>卡号</th><th>出站事件</th><th>时刻</th><th>状态</th><th>选择</th></tr>
            </thead>
            <tbody>
              {旁路.map((r) => (
                <tr key={r.编号}>
                  <td>{r.编号}</td><td>{r.卡号}</td><td>{r.事件编号}</td>
                  <td>{r.时刻}</td>
                  <td><span className={`徽章 ${r.状态 === "开" ? "败" : "通"}`}>{r.状态}</span></td>
                  <td>
                    <button className="次 亮片" onClick={() => 设选旁路(String(r.编号))}>
                      {String(r.编号) === String(选旁路) ? "已选" : "选它"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {当前旁路 && (
        <div className="段">
          <div className="段题">补录 · 旁路 #{当前旁路.编号}（{当前旁路.卡号}）</div>
          <div className="行">
            <label>
              补录进站站：{" "}
              <select value={站键} onChange={(e) => 设站键(e.target.value)}>
                <option value="">— 必须选择 —</option>
                {站.map((s) => (
                  <option key={s.站点键} value={s.站点键}>
                    {s.站点键} · {s.站名}（{s.线路键} 序{s.站序}）
                  </option>
                ))}
              </select>
            </label>
            <label>
              请求编号（幂等）：{" "}
              <input
                value={请求号}
                onChange={(e) => 设请求号(e.target.value)}
                placeholder="可留空"
                style={{ width: 140 }}
              />
            </label>
            <button onClick={补录} disabled={!开 || !站键}>经闸补录</button>
          </div>
          {预 && (
            <table>
              <thead>
                <tr><th>valid</th><th>闸</th><th>虚进站</th><th>行程</th><th>拒绝</th></tr>
              </thead>
              <tbody>
                <tr>
                  <td><span className={`徽章 ${预.valid ? "通" : "败"}`}>{预.valid ? "可补录" : "不可"}</span></td>
                  <td>{预.闸开关}</td>
                  <td>{预.虚进站 || "—"}</td>
                  <td>{预.行程 ? `${预.行程.进站站点键}→${预.行程.出站站点键}` : "—"}</td>
                  <td>{预.拒绝 || "—"}</td>
                </tr>
              </tbody>
            </table>
          )}
        </div>
      )}

      <div className="段">
        <div className="段题">补录审计账</div>
        {!账.length ? (
          <div className="空态">尚无补录审计记录。</div>
        ) : (
          <table>
            <thead>
              <tr><th>#</th><th>时刻</th><th>闸</th><th>旁路</th><th>卡号</th><th>虚进站</th><th>结果</th><th>口径</th><th>拒绝原因</th></tr>
            </thead>
            <tbody>
              {账.map((r) => (
                <tr key={r.编号}>
                  <td>{r.编号}</td><td>{r.时刻}</td><td>{r.闸态}</td>
                  <td>{r.旁路编号 || "—"}</td><td>{r.卡号 || "—"}</td>
                  <td>{r.补录站点键 || "—"}</td>
                  <td><span className={`徽章 ${r.结果 === "已成对" ? "通" : "败"}`}>{r.结果}</span></td>
                  <td>{r.审计口径}</td><td>{r.拒绝原因 || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

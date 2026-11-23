import React, { useEffect, useState } from "react";
import { 取, 递 } from "../api.js";

const 夹具 = ["成对样例", "缺腿超时样例", "出站孤儿样例", "重复进站样例"];

export default function 刷卡流() {
  const [行, 设行] = useState([]);
  const [讯, 设讯] = useState("");
  const 刷 = () => 取("/刷卡点").then(设行);
  useEffect(() => { 刷(); }, []);
  const 灌 = async (名) => {
    设讯("装载中…");
    try {
      const r = await 递(`/装载/夹具?名=${encodeURIComponent(名)}`);
      设讯(`批次 ${r.批次编号}：入流${r.入流} 开腿${r.开腿} 成对${r.成对} 旁路${r.旁路}`);
      await 刷();
    } catch (e) {
      设讯(String(e.message || e));
    }
  };
  return (
    <div>
      <h1 className="题">刷卡流</h1>
      <p className="述">从夹具灌进出闸事件。看命运：已开腿 / 已成对 / 已旁路。</p>
      <div className="行">
        {夹具.map((n) => (
          <button key={n} className="次 亮片" onClick={() => 灌(n)}>{n}</button>
        ))}
        <button className="次" onClick={刷}>刷新</button>
      </div>
      {讯 && <p className="讯">{讯}</p>}
      {!行.length ? (
        <div className="空态">尚无刷卡点。先灌「成对样例」。</div>
      ) : (
        <table>
          <thead>
            <tr>
              <th>事件编号</th><th>卡号</th><th>站点</th><th>方向</th><th>事件时</th><th>命运</th><th>行程键</th>
            </tr>
          </thead>
          <tbody>
            {行.map((r) => (
              <tr key={r.事件编号}>
                <td>{r.事件编号}</td><td>{r.卡号}</td><td>{r.站点键}</td><td>{r.方向}</td>
                <td>{r.事件时}</td><td>{r.命运}</td><td>{r.行程键 || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

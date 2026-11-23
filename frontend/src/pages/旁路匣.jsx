import React, { useEffect, useState } from "react";
import { 取 } from "../api.js";

export default function 旁路匣() {
  const [行, 设] = useState([]);
  const 刷 = () => 取("/旁路匣").then(设);
  useEffect(() => { 刷(); }, []);
  return (
    <div>
      <h1 className="题">旁路匣</h1>
      <p className="述">缺腿超时、出站孤儿、重复进站、未知站等旁路原因。</p>
      <div className="行"><button className="次" onClick={刷}>刷新</button></div>
      {!行.length ? <div className="空态">旁路匣空。</div> : (
        <table>
          <thead><tr><th>#</th><th>原因</th><th>卡号</th><th>事件</th><th>时刻</th><th>载荷</th></tr></thead>
          <tbody>
            {行.map((r) => (
              <tr key={r.编号}>
                <td>{r.编号}</td><td>{r.原因}</td><td>{r.卡号}</td>
                <td>{r.事件编号}</td><td>{r.时刻}</td>
                <td style={{ maxWidth: 360, wordBreak: "break-all" }}>{r.载荷}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

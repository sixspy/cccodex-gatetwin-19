import React, { useEffect, useState } from "react";
import { 取 } from "../api.js";

export default function 线路站() {
  const [行, 设] = useState([]);
  useEffect(() => { 取("/线路").then(设); }, []);
  return (
    <div>
      <h1 className="题">线路站</h1>
      <p className="述">种子线路与站点。未知站点刷卡会进旁路。</p>
      {!行.length ? <div className="空态">无线路。</div> : 行.map((ln) => (
        <div className="段" key={ln.线路键}>
          <div className="段题">{ln.线路键} · {ln.名称}</div>
          <table>
            <thead><tr><th>站点键</th><th>站名</th><th>站序</th></tr></thead>
            <tbody>
              {(ln.站点 || []).map((s) => (
                <tr key={s.站点键}><td>{s.站点键}</td><td>{s.站名}</td><td>{s.站序}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  );
}

import React, { useEffect, useState } from "react";
import { 取 } from "../api.js";

export default function 站规() {
  const [规, 设] = useState(null);
  useEffect(() => { 取("/站规").then(设); }, []);
  if (!规) return <p className="讯">加载中…</p>;
  return (
    <div>
      <h1 className="题">站规</h1>
      <p className="述">配对与超时等口径。邻题可在空桩改写策略，勿默默改坏 happy path。</p>
      <table>
        <thead><tr><th>键</th><th>值</th></tr></thead>
        <tbody>
          {Object.entries(规).map(([k, v]) => (
            <tr key={k}><td>{k}</td><td>{v}</td></tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

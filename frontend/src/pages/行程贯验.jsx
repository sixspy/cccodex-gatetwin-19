import React, { useEffect, useState } from "react";
import { 取, 递 } from "../api.js";

export default function 行程贯验() {
  const [史, 设史] = useState([]);
  const [末, 设末] = useState(null);
  const 刷 = () => 取("/贯验").then(设史);
  useEffect(() => { 刷(); }, []);
  const 跑 = async () => {
    const r = await 递("/贯验");
    设末(r);
    await 刷();
  };
  return (
    <div>
      <h1 className="题">行程贯验</h1>
      <p className="述">校验：每笔行程对应两笔已成对刷卡；已开腿刷卡数=在途开腿。</p>
      <div className="行">
        <button onClick={跑}>跑贯验</button>
        <button className="次" onClick={刷}>刷新历史</button>
      </div>
      {末 && (
        <div className="行" style={{ gap: "0.7rem" }}>
          <span className={`徽章 ${末.是否通过 ? "通" : "败"}`}>{末.是否通过 ? "对齐" : "撕裂"}</span>
          <span className="讯" style={{ margin: 0 }}>{末.说明}</span>
        </div>
      )}
      {!史.length ? <div className="空态">尚无贯验记录。</div> : (
        <table>
          <thead>
            <tr><th>#</th><th>时刻</th><th>刷卡</th><th>行程</th><th>开腿</th><th>旁路</th><th>结果</th><th>说明</th></tr>
          </thead>
          <tbody>
            {史.map((r) => (
              <tr key={r.编号}>
                <td>{r.编号}</td><td>{r.时刻}</td><td>{r.刷卡数}</td><td>{r.行程数}</td>
                <td>{r.开腿数}</td><td>{r.旁路数}</td>
                <td><span className={`徽章 ${r.是否通过 ? "通" : "败"}`}>{r.是否通过 ? "通" : "败"}</span></td>
                <td>{r.说明}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

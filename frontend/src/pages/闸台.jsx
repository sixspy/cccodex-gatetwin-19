import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { 取 } from "../api.js";

export default function 闸台() {
  const [数, 设] = useState(null);
  const 刷 = () => 取("/总览").then(设);
  useEffect(() => { 刷(); }, []);
  if (!数) return <p className="讯">加载中…</p>;
  const 末 = 数.末次贯验;
  return (
    <div>
      <h1 className="题">闸台</h1>
      <p className="述">
        主路径：刷卡按<strong>同卡</strong>先进后出<strong>成对</strong> → 进站写入<strong>开腿账</strong> →
        出站落<strong>行程账</strong> → 缺腿超时 / 出站孤儿进<strong>旁路匣</strong> → 行程与刷卡互证。
      </p>
      <div className="阶条">
        <div className="阶"><div className="序">① 刷卡</div><b>{数.刷卡点 ?? 0}</b><span>已见事件</span></div>
        <div className="阶"><div className="序">② 开腿</div><b>{数.在途开腿 ?? 0}</b><span>在途</span></div>
        <div className="阶"><div className="序">③ 行程</div><b>{数.行程数 ?? 0}</b><span>已成对</span></div>
        <div className="阶"><div className="序">④ 旁路</div><b>{数.旁路匣 ?? 0}</b><span>旁路匣</span></div>
        <div className="阶"><div className="序">⑤ 成对刷卡</div><b>{数.已成对 ?? 0}</b><span>命运=已成对</span></div>
      </div>
      <div className="提示条">
        冒烟：<Link to="/刷卡流">刷卡流</Link> 依次推成对 / 缺腿超时 / 出站孤儿 → 看开腿账与行程账 →{" "}
        <Link to="/行程贯验">行程贯验</Link>。
      </div>
      <div className="行"><button className="次" onClick={刷}>刷新台面</button></div>
      {末 ? (
        <div className="行" style={{ gap: "0.7rem" }}>
          <span>最近行程贯验</span>
          <span className={`徽章 ${末.是否通过 ? "通" : "败"}`}>{末.是否通过 ? "对齐" : "撕裂"}</span>
          <span className="讯" style={{ margin: 0 }}>{末.说明}</span>
        </div>
      ) : (
        <div className="空态">还没跑过行程贯验。先推刷卡流，再去「行程贯验」。</div>
      )}
    </div>
  );
}

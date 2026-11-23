import React from "react";
import { NavLink, Route, Routes } from "react-router-dom";
import 闸台 from "./pages/闸台.jsx";
import 刷卡流 from "./pages/刷卡流.jsx";
import 开腿账 from "./pages/开腿账.jsx";
import 行程账 from "./pages/行程账.jsx";
import 旁路匣 from "./pages/旁路匣.jsx";
import 行程贯验 from "./pages/行程贯验.jsx";
import 站规 from "./pages/站规.jsx";
import 线路站 from "./pages/线路站.jsx";

const 主链 = [
  ["/", "闸台"],
  ["/刷卡流", "① 刷卡流"],
  ["/开腿账", "② 开腿账"],
  ["/行程账", "③ 行程账"],
  ["/旁路匣", "④ 旁路匣"],
  ["/行程贯验", "行程贯验"],
];
const 次链 = [["/站规", "站规"], ["/线路站", "线路站"]];

export default function App() {
  return (
    <div className="壳">
      <header className="顶栏">
        <div className="顶上行">
          <div className="牌名">闸对</div>
          <div className="牌骨">刷卡入流 → 同卡进站开腿 / 出站成对 → 缺腿超时旁路 → 行程互证</div>
        </div>
        <nav className="管线">
          {主链.map(([to, l]) => (
            <NavLink key={to} to={to} end={to === "/"} className={({ isActive }) => (isActive ? "亮" : "")}>
              {l}
            </NavLink>
          ))}
          {次链.map(([to, l]) => (
            <NavLink key={to} to={to} className={({ isActive }) => (isActive ? "亮 次链" : "次链")}>
              {l}
            </NavLink>
          ))}
        </nav>
      </header>
      <main className="主">
        <Routes>
          <Route path="/" element={<闸台 />} />
          <Route path="/刷卡流" element={<刷卡流 />} />
          <Route path="/开腿账" element={<开腿账 />} />
          <Route path="/行程账" element={<行程账 />} />
          <Route path="/旁路匣" element={<旁路匣 />} />
          <Route path="/行程贯验" element={<行程贯验 />} />
          <Route path="/站规" element={<站规 />} />
          <Route path="/线路站" element={<线路站 />} />
        </Routes>
      </main>
    </div>
  );
}

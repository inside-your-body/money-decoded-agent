// Style sample for the Persian channel (owner Nov 8): flat 2D motion graphics + professional Persian kinetic typography. Not used by the bot yet.
import React from 'react';
import {AbsoluteFill, useCurrentFrame, spring, interpolate, Easing} from 'remotion';
import './theme';

const C = {cream: '#FFF4E3', navy: '#14213D', ink: '#1B263B', orange: '#FB8500', yellow: '#FFB703', red: '#E63946', teal: '#2A9D8F', sky: '#8ECAE6', white: '#FFFFFF'};
const cl = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};
const sp = (f: number, at: number, d = 14, s = 160) => spring({frame: f - at, fps: 30, config: {damping: d, stiffness: s}});
const ease = (f: number, a: number, b: number) => interpolate(f, [a, b], [0, 1], {...cl, easing: Easing.bezier(0.22, 1, 0.36, 1)});

// one word that rises out of a mask (professional kinetic type)
const Rise: React.FC<{text: string; f: number; at: number; size: number; color?: string; weight?: string; marker?: string; mAt?: number}> =
  ({text, f, at, size, color = C.ink, weight = 'F_vazirb', marker, mAt}) => {
  const k = ease(f, at, at + 14);
  const m = marker ? ease(f, mAt ?? at + 10, (mAt ?? at + 10) + 12) : 0;
  return <span style={{display: 'inline-block', overflow: 'hidden', padding: `0 ${size * 0.08}px`, lineHeight: 1.35, verticalAlign: 'bottom', position: 'relative'}}>
    {marker && <span style={{position: 'absolute', right: 0, bottom: size * 0.18, height: size * 0.42, width: `${m * 100}%`, background: marker, borderRadius: size * 0.08}} />}
    <span style={{display: 'inline-block', position: 'relative', transform: `translateY(${(1 - k) * 110}%)`, fontFamily: weight, fontSize: size, color}}>{text}</span>
  </span>;
};

const Line: React.FC<{children: React.ReactNode; top: number; size?: number}> = ({children, top}) =>
  <div style={{position: 'absolute', top, left: 0, right: 0, display: 'flex', justifyContent: 'center', direction: 'rtl', gap: 18, flexWrap: 'wrap'}}>{children}</div>;

// ---- flat icons (centre 0,0, about ±100) ----
const Wallet = () => <g><rect x={-110} y={-70} width={220} height={150} rx={26} fill={C.teal} /><rect x={-110} y={-70} width={220} height={40} rx={20} fill="#21867A" />
  <rect x={30} y={-5} width={90} height={56} rx={16} fill="#21867A" /><circle cx={62} cy={23} r={12} fill={C.yellow} /></g>;
const Car = () => <g><path d="M-120 20 Q-110 -30 -60 -40 L40 -40 Q80 -40 100 -5 L125 10 Q135 20 130 40 L-120 40 Z" fill={C.red} />
  <path d="M-55 -32 L-10 -32 L-10 -5 L-75 -5 Z" fill={C.sky} /><path d="M0 -32 L40 -32 Q65 -30 80 -5 L0 -5 Z" fill={C.sky} />
  <circle cx={-65} cy={45} r={26} fill={C.navy} /><circle cx={-65} cy={45} r={10} fill="#ccc" /><circle cx={75} cy={45} r={26} fill={C.navy} /><circle cx={75} cy={45} r={10} fill="#ccc" /></g>;
const House = () => <g><path d="M-110 -10 L0 -100 L110 -10 Z" fill={C.orange} /><rect x={-85} y={-15} width={170} height={115} fill={C.yellow} />
  <rect x={-20} y={35} width={44} height={65} rx={6} fill={C.navy} /><rect x={-70} y={10} width={36} height={32} rx={4} fill={C.sky} /><rect x={36} y={10} width={36} height={32} rx={4} fill={C.sky} /></g>;
const Coins = () => <g>{[0, 1, 2, 3].map((i) => <g key={i} transform={`translate(${i % 2 ? 40 : -40} ${40 - Math.floor(i / 2) * 0 - i * 22})`}>
  <ellipse rx={62} ry={18} cy={10} fill="#C98A00" /><ellipse rx={62} ry={18} fill={C.yellow} /></g>)}</g>;
const Note: React.FC<{w?: number}> = ({w = 1}) => <g transform={`scale(${w} 1)`}><rect x={-150} y={-75} width={300} height={150} rx={18} fill="#6BBF59" />
  <rect x={-132} y={-57} width={264} height={114} rx={12} fill="none" stroke="#3F8F35" strokeWidth={6} /><circle r={36} fill="#3F8F35" /></g>;

// circle wipe into the next scene
const Wipe: React.FC<{f: number; at: number; color: string; x?: number; y?: number}> = ({f, at, color, x = 960, y = 540}) => {
  const k = ease(f, at, at + 16);
  return k > 0 ? <svg width={1920} height={1080} style={{position: 'absolute'}}><circle cx={x} cy={y} r={k * 2300} fill={color} /></svg> : null;
};

const Brand: React.FC<{dark?: boolean}> = ({dark}) => <div style={{position: 'absolute', top: 40, left: 56, direction: 'rtl', fontFamily: 'F_vazir', fontSize: 30,
  color: dark ? 'rgba(255,255,255,0.75)' : 'rgba(20,33,61,0.6)', display: 'flex', alignItems: 'center', gap: 12}}>
  <span style={{width: 18, height: 18, borderRadius: 9, background: C.orange, display: 'inline-block'}} />پول و قدرت</div>;

const Scene1: React.FC<{f: number}> = ({f}) => {
  const n = Math.round(100 * ease(f, 30, 75));
  const w = sp(f, 18);
  return <AbsoluteFill style={{background: C.cream}}>
    <Brand />
    <Line top={170}><Rise text="ده" f={f} at={4} size={70} color={C.teal} /><Rise text="سال" f={f} at={8} size={70} color={C.teal} /><Rise text="پیش..." f={f} at={12} size={70} color={C.teal} /></Line>
    <div style={{position: 'absolute', top: 290, left: 0, right: 0, textAlign: 'center', direction: 'rtl', fontFamily: 'F_vazirb', fontSize: 230, color: C.navy, lineHeight: 1.2}}>
      {n}<span style={{fontSize: 110}}> میلیون</span></div>
    <Line top={620}><Rise text="تومان" f={f} at={70} size={96} marker={C.yellow} mAt={78} /><Rise text="پس‌انداز" f={f} at={74} size={96} /><Rise text="داشتی" f={f} at={78} size={96} /></Line>
    <svg width={1920} height={1080} style={{position: 'absolute'}}><g transform={`translate(330 560) scale(${w}) rotate(${(1 - Math.min(1, w)) * -20})`}><Wallet /></g>
      <g transform={`translate(1600 520) scale(${sp(f, 40)})`}><Coins /></g></svg>
  </AbsoluteFill>;
};

const Scene2: React.FC<{f: number}> = ({f}) => {
  const items = [{el: <Car />, t: 'یک ماشین', c: C.red}, {el: <House />, t: 'رهن یک خانه', c: C.orange}, {el: <Coins />, t: '۲۵ سکه طلا', c: C.yellow}];
  return <AbsoluteFill style={{background: C.cream}}>
    <Brand />
    <Line top={110}><Rise text="با" f={f} at={2} size={88} /><Rise text="همین" f={f} at={6} size={88} /><Rise text="پول" f={f} at={10} size={88} marker={C.sky} /><Rise text="می‌شد" f={f} at={14} size={88} /><Rise text="خرید:" f={f} at={18} size={88} /></Line>
    {items.map((it, i) => {
      const k = sp(f, 28 + i * 12, 12, 140); const x = 1450 - i * 490;
      return <div key={i} style={{position: 'absolute', left: x - 200, top: 380 + (1 - Math.min(1, k)) * 120, width: 400, height: 470, borderRadius: 36, background: C.white,
        boxShadow: '0 24px 0 rgba(20,33,61,0.08)', opacity: Math.min(1, k * 1.4), transform: `scale(${0.85 + 0.15 * Math.min(1, k)})`}}>
        <svg width={400} height={300}><g transform="translate(200 160) scale(1.25)">{it.el}</g></svg>
        <div style={{textAlign: 'center', direction: 'rtl', fontFamily: 'F_vazirb', fontSize: 58, color: C.ink}}>{it.t}</div>
        <div style={{position: 'absolute', top: 24, right: 24, width: 56, height: 56, borderRadius: 28, background: it.c, color: C.white, fontFamily: 'F_vazirb',
          fontSize: 36, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>✓</div>
      </div>;
    })}
  </AbsoluteFill>;
};

const Scene3: React.FC<{f: number}> = ({f}) => {
  const bars = [{y: 'سال ۱', v: 0.12}, {y: 'سال ۳', v: 0.22}, {y: 'سال ۵', v: 0.38}, {y: 'سال ۷', v: 0.62}, {y: 'سال ۱۰', v: 1}];
  return <AbsoluteFill style={{background: C.navy}}>
    <Brand dark />
    <div style={{position: 'absolute', top: 120, right: 140, direction: 'rtl'}}>
      <Rise text="امروز؟" f={f} at={4} size={150} color={C.white} />
      <div style={{marginTop: 10}}><Rise text="قیمت" f={f} at={14} size={74} color={C.sky} /><Rise text="همه‌چیز" f={f} at={18} size={74} color={C.sky} /><Rise text="چند" f={f} at={22} size={74} color={C.yellow} /><Rise text="برابر" f={f} at={26} size={74} color={C.yellow} /><Rise text="شد" f={f} at={30} size={74} color={C.sky} /></div>
    </div>
    <svg width={1920} height={1080} style={{position: 'absolute'}}>
      <line x1={140} y1={940} x2={1000} y2={940} stroke="rgba(255,255,255,0.3)" strokeWidth={4} />
      {bars.map((b, i) => {
        const k = ease(f, 20 + i * 8, 44 + i * 8); const h = 640 * b.v * k; const x = 180 + i * 165;
        return <g key={i}><rect x={x} y={940 - h} width={110} height={h} rx={14} fill={i === bars.length - 1 ? C.red : C.orange} opacity={0.35 + 0.65 * (i + 1) / bars.length} />
          <text x={x + 55} y={990} textAnchor="middle" direction="rtl" fontFamily="F_vazir" fontSize={34} fill="rgba(255,255,255,0.8)">{b.y}</text></g>;
      })}
    </svg>
  </AbsoluteFill>;
};

const Scene4: React.FC<{f: number}> = ({f}) => {
  const strike = ease(f, 30, 44); const shrink = 1 - 0.4 * ease(f, 50, 80);
  return <AbsoluteFill style={{background: C.cream}}>
    <Brand />
    <Line top={210}><Rise text="پول" f={f} at={2} size={120} /><Rise text="تو" f={f} at={6} size={120} /><Rise text="کم" f={f} at={10} size={120} /><Rise text="نشد..." f={f} at={14} size={120} /></Line>
    <svg width={1920} height={1080} style={{position: 'absolute'}}><line x1={1400} y1={330} x2={1400 - 880 * strike} y2={330} stroke={C.red} strokeWidth={16} strokeLinecap="round" /></svg>
    <Line top={470}><Rise text="ارزشش" f={f} at={44} size={150} color={C.red} marker={C.yellow} mAt={56} /><Rise text="آب" f={f} at={50} size={150} /><Rise text="شد" f={f} at={54} size={150} /></Line>
    <svg width={1920} height={1080} style={{position: 'absolute'}}><g transform={`translate(960 900) scale(${shrink * 0.9})`} opacity={0.95}><Note /></g></svg>
  </AbsoluteFill>;
};

const Scene5: React.FC<{f: number}> = ({f}) => {
  const q = sp(f, 30, 9, 120);
  return <AbsoluteFill style={{background: C.orange}}>
    <Line top={300}><Rise text="پس" f={f} at={4} size={140} color={C.white} /><Rise text="این" f={f} at={8} size={140} color={C.white} /><Rise text="پول" f={f} at={12} size={140} color={C.white} /><Rise text="کجا" f={f} at={16} size={140} color={C.navy} /><Rise text="رفت" f={f} at={20} size={140} color={C.white} /></Line>
    <div style={{position: 'absolute', top: 470, left: 0, right: 0, textAlign: 'center', fontFamily: 'F_vazirb', fontSize: 260, color: C.navy, transform: `scale(${q}) rotate(${Math.sin(f / 8) * 4}deg)`}}>؟</div>
    <div style={{position: 'absolute', bottom: 60, left: 0, right: 0, textAlign: 'center', direction: 'rtl', fontFamily: 'F_vazir', fontSize: 38, color: C.white, opacity: ease(f, 40, 55)}}>پول و قدرت — پول واقعاً چطور کار می‌کند</div>
  </AbsoluteFill>;
};

export const FaSample: React.FC = () => {
  const f = useCurrentFrame();
  const S = [0, 120, 230, 345, 450];
  const idx = S.filter((s) => f >= s).length - 1;
  const lf = f - S[idx];
  const scenes = [Scene1, Scene2, Scene3, Scene4, Scene5];
  const Cur = scenes[idx];
  const next = [C.cream, C.navy, C.cream, C.orange];
  return <AbsoluteFill>
    <Cur f={lf} />
    {idx < 4 && <Wipe f={f} at={S[idx + 1] - 16} color={next[idx]} x={idx % 2 ? 300 : 1620} y={idx % 2 ? 900 : 200} />}
  </AbsoluteFill>;
};

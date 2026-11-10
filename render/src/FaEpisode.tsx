// Persian channel engine (owner approved the sample, Nov 8 2026): flat 2D motion graphics + professional Persian kinetic typography.
// No mascot drawings: every sentence = 1-4 key words rising out of a mask (key word on a coloured marker) + one flat widget.
// Each section (stage) has its own flat background; a circle wipe opens every new section. Long 1920x1080, Short 1080x1920.
import React from 'react';
import {AbsoluteFill, useCurrentFrame, spring, interpolate, Easing} from 'remotion';
import {iconPath} from './Icons';
import type {TLEpProps, Visual} from './TLEpisode';
import './theme';

export const C = {cream: '#FFF4E3', navy: '#14213D', ink: '#1B263B', orange: '#FB8500', yellow: '#FFB703', red: '#E63946', teal: '#2A9D8F',
  sky: '#8ECAE6', white: '#FFFFFF', mint: '#EAF5EF'};
type Th = {bg: string; ink: string; sub: string; card: string; cardInk: string; marker: string; accent: string};
// owner (Nov 9): a different colour palette for every topic -> props.palette picks one set (light, dark, tint + the hook colour)
const mk = (light: string, dark: string, tint: string, hook: string, acc: string, mark: string): Th[] => [
  {bg: light, ink: C.ink, sub: '#6B7A90', card: C.white, cardInk: C.ink, marker: mark, accent: acc},
  {bg: dark, ink: C.white, sub: '#A9B8CF', card: 'rgba(255,255,255,0.10)', cardInk: C.white, marker: acc, accent: mark},
  {bg: tint, ink: C.ink, sub: '#5F6F74', card: C.white, cardInk: C.ink, marker: mark, accent: acc},
  {bg: hook, ink: C.white, sub: 'rgba(255,255,255,0.8)', card: C.white, cardInk: C.ink, marker: dark, accent: dark},
];
const PALETTES: Th[][] = [
  mk(C.cream, C.navy, C.mint, C.orange, C.orange, C.yellow),
  mk('#F4F1FF', '#1E1B4B', '#E8F7F4', '#7C3AED', '#7C3AED', '#FBBF24'),
  mk('#FFF1F0', '#2B1B2E', '#FFF7E6', '#E63946', '#E63946', '#FFB703'),
  mk('#EEF6FF', '#0B2545', '#E9F5EC', '#1D6FE0', '#1D6FE0', '#FFD166'),
  mk('#F1F8E9', '#1B3A2B', '#FFF8E1', '#2A9D8F', '#2A9D8F', '#F4A261'),
  mk('#FFF8EC', '#3A2412', '#EEF5FF', '#D97706', '#D97706', '#FDE68A'),
];
// owner: no Latin digits on screen -> Persian digits everywhere; % -> ٪
export const P = (t: any) => (typeof t === 'string' || typeof t === 'number') ? String(t).replace(/[0-9]/g, (d) => '۰۱۲۳۴۵۶۷۸۹'[+d]).replace(/%/g, '٪').replace(/,/g, '٬').replace(/\./g, '٫') : t;

const cl = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};
const sp = (f: number, at: number, d = 14, s = 160) => spring({frame: f - at, fps: 30, config: {damping: d, stiffness: s}});
const ease = (f: number, a: number, b: number) => interpolate(f, [a, b], [0, 1], {...cl, easing: Easing.bezier(0.22, 1, 0.36, 1)});
const fmt = (v: number) => P(Math.abs(v) >= 1000 ? Math.round(v).toLocaleString('en-US') : (Math.abs(v) < 10 && v % 1 ? v.toFixed(1) : String(Math.round(v))));
const CUR: Record<string, string> = {'$': 'دلار', '€': 'یورو', '£': 'پوند', '¥': 'ین'};
// currency symbols are written as words after the number (no Latin symbols on screen)
const cur = (_u?: string) => '';
const rest = (u?: string, pre?: string) => { const c = CUR[(pre || '').trim()] || CUR[(u || '')[0]] || ''; const r0 = (u || '').replace(/^[$£€¥]/, '').trim(); return P([r0, c].filter(Boolean).join(' ')); };

// ---------- kinetic typography ----------
const Rise: React.FC<{text: string; f: number; at: number; size: number; color: string; marker?: string}> = ({text, f, at, size, color, marker}) => {
  const k = ease(f, at, at + 13);
  const m = marker ? ease(f, at + 9, at + 21) : 0;
  return <span style={{display: 'inline-block', overflow: 'hidden', padding: `0 ${size * 0.1}px`, lineHeight: 1.38, position: 'relative'}}>
    {marker && <span style={{position: 'absolute', right: 0, bottom: size * 0.2, height: size * 0.42, width: `${m * 100}%`, background: marker, borderRadius: size * 0.08}} />}
    <span style={{display: 'inline-block', position: 'relative', transform: `translateY(${(1 - k) * 112}%)`, fontFamily: 'F_lalezar', fontSize: size, color}}>{P(text)}</span>
  </span>;
};

const KWords: React.FC<{words: string[]; f: number; at: number; size: number; th: Th; top: number; width: number; left: number}> = ({words, f, at, size, th, top, width, left}) => {
  const ws = words.join(' ').split(/\s+/).filter(Boolean).slice(0, 7);
  const n = ws.length;
  return <div style={{position: 'absolute', top, left, width, display: 'flex', flexWrap: 'wrap', justifyContent: 'center', direction: 'rtl', columnGap: size * 0.12}}>
    {ws.map((w, i) => <Rise key={i} text={w} f={f} at={at + i * 4} size={size} color={th.ink} marker={i === n - 1 && n > 1 ? th.marker : undefined} />)}
  </div>;
};

// flat badge: coloured circle with a thick white icon
const Badge: React.FC<{name: string; x: number; y: number; r: number; color: string; k?: number; cross?: boolean}> = ({name, x, y, r, color, k = 1, cross}) =>
  <g transform={`translate(${x} ${y}) scale(${Math.max(0, k)})`}>
    <circle r={r} cy={r * 0.08} fill="rgba(0,0,0,0.12)" />
    <circle r={r} fill={color} />
    <g transform={`scale(${(r * 1.15) / 100}) translate(-50 -50)`}>
      <path d={iconPath(name)} fill="none" stroke="#FFFFFF" strokeWidth={7} strokeLinecap="round" strokeLinejoin="round" /></g>
    {cross && <g stroke={C.red} strokeWidth={r * 0.16} strokeLinecap="round"><line x1={-r * 0.8} y1={-r * 0.8} x2={r * 0.8} y2={r * 0.8} /><line x1={r * 0.8} y1={-r * 0.8} x2={-r * 0.8} y2={r * 0.8} /></g>}
  </g>;

const Card: React.FC<{x: number; y: number; w: number; h: number; th: Th; children?: React.ReactNode}> = ({x, y, w, h, th, children}) =>
  <g><rect x={x} y={y + 10} width={w} height={h} rx={30} fill="rgba(0,0,0,0.10)" /><rect x={x} y={y} width={w} height={h} rx={30} fill={th.card} />{children}</g>;

const T: React.FC<{x?: number; y: number; size: number; fill: string; children: React.ReactNode; anchor?: 'middle' | 'start' | 'end'; o?: number; bold?: boolean}> =
  ({x = 0, y, size, fill, children, anchor = 'middle', o = 1, bold = true}) =>
  <text x={x} y={y} direction="rtl" textAnchor={anchor} fontFamily={bold ? 'F_titr' : 'F_yekan'} fontSize={size} fill={fill} opacity={o}>{P(children)}</text>;

// flat money map: 8 places around "you"; the place we talk about grows and coins fly to it
const PLACES: Record<string, {label: string; icon: string; a: number; c: string}> = {
  central_bank: {label: 'بانک مرکزی', icon: 'vault', a: -90, c: C.yellow}, bank: {label: 'بانک', icon: 'bank', a: -45, c: C.teal},
  market: {label: 'بازار', icon: 'chartup', a: 0, c: '#219EBC'}, company: {label: 'شرکت‌ها', icon: 'factory', a: 45, c: '#8338EC'},
  home: {label: 'مسکن', icon: 'house', a: 90, c: C.orange}, debt: {label: 'بدهی', icon: 'card', a: 135, c: C.red},
  government: {label: 'دولت', icon: 'capitol', a: 180, c: '#3A86FF'}, gold: {label: 'طلا', icon: 'gold', a: -135, c: '#E0A100'},
};
const FlatMap: React.FC<{focus: string; label?: string; f: number; at: number; th: Th}> = ({focus, label, f, at, th}) => {
  const R = 175; const k = sp(f, at);
  const pos = (n: string) => { const p = PLACES[n]; if (!p) return [0, 0]; const a = (p.a * Math.PI) / 180; return [Math.cos(a) * R * 1.45, Math.sin(a) * R]; };
  const [tx, ty] = pos(focus);
  return <g>
    {Object.keys(PLACES).map((n) => { const [x, y] = pos(n); const on = n === focus;
      return <g key={n}><line x1={0} y1={0} x2={x} y2={y} stroke={on ? PLACES[n].c : th.sub} strokeOpacity={on ? 0.9 : 0.3} strokeWidth={on ? 6 : 3} strokeDasharray={on ? '0' : '6 10'} />
        <Badge name={PLACES[n].icon} x={x} y={y} r={on ? 44 + 10 * k : 34} color={on ? PLACES[n].c : th.sub} />
        <T x={x} y={y + (on ? 92 : 70)} size={on ? 30 : 22} fill={on ? th.ink : th.sub}>{PLACES[n].label}</T></g>; })}
    <Badge name="person" x={0} y={0} r={focus === 'you' ? 62 : 50} color={C.navy === th.bg ? C.orange : C.navy} />
    <T y={88} size={26} fill={th.ink}>شما</T>
    {focus in PLACES && [0, 1, 2, 3].map((j) => { const t = ((f - at) / 32 + j / 4) % 1; if (f < at + j * 4) return null;
      return <circle key={j} cx={tx * t} cy={ty * t - Math.sin(t * Math.PI) * 40} r={11} fill={C.yellow} stroke="#C98A00" strokeWidth={3} />; })}
    {label && <T y={300} size={40} fill={th.ink}>{label}</T>}
  </g>;
};

// ---------- widgets (inside a ±390 x ±250 box) ----------
const Widget: React.FC<{v: Visual; f: number; at: number; dur: number; th: Th; node: string}> = ({v, f, at, dur, th, node}) => {
  const p = sp(f, at), t = ease(f, at + 4, at + Math.min(60, dur * 0.7));
  const lab = (txt: string | undefined, y: number) => txt ? <T y={y} size={40} fill={th.sub} o={ease(f, at + 10, at + 22)}>{txt.slice(0, 40)}</T> : null;
  switch (v.type) {
    case 'stat': {
      const col = v.good === false ? C.red : v.good ? C.teal : C.orange;
      const val = fmt((v.value || 0) * t); const u = rest(v.unit, v.prefix);
      const len = (v.prefix || '').length + val.length + u.length;
      const size = len > 12 ? 120 : len > 8 ? 150 : 190;
      return <g transform={`scale(${0.85 + 0.15 * Math.min(1, p)})`}>
        <Card x={-390} y={-150} w={780} h={260} th={{...th, card: C.white}} />
        <rect x={-300 * ease(f, at + 8, at + 24)} y={-10} width={600 * ease(f, at + 8, at + 24)} height={60} rx={14} fill={C.yellow} opacity={0.45} />
        <text y={40} direction="rtl" textAnchor="middle" fontFamily="F_titr" fontSize={size} fill={col}>
          {val}{rest(v.unit, v.prefix) ? <tspan fontSize={size * 0.42}>{' ' + rest(v.unit, v.prefix)}</tspan> : null}</text>
        {lab(v.label, 190)}
      </g>;
    }
    case 'chart': {
      const S: Record<string, (x: number) => number> = {rise: (x) => 0.15 + 0.7 * x, fall: (x) => 0.85 - 0.7 * x,
        crash: (x) => (x < 0.6 ? 0.6 + 0.3 * x : 0.78 - 0.65 * Math.min(1, (x - 0.6) / 0.15)), bubble: (x) => (x < 0.7 ? 0.12 + 0.8 * Math.pow(x / 0.7, 3) : 0.92 - 0.8 * Math.min(1, (x - 0.7) / 0.15)),
        recover: (x) => (x < 0.35 ? 0.75 - 1.6 * x : 0.19 + 0.75 * (x - 0.35) / 0.65), zigzag: (x) => 0.5 + 0.28 * Math.sin(x * 13), flat: (x) => 0.5};
      const fn = S[v.shape] || S.zigzag; const n = 40; const m = Math.max(1, Math.round(n * t));
      const bad = ['fall', 'crash'].includes(v.shape);
      return <g opacity={Math.min(1, p * 1.5)}><Card x={-380} y={-230} w={760} h={400} th={th}>
        {Array.from({length: m}).map((_, i) => { const x = -340 + (680 / n) * i; const h = 320 * fn(i / n);
          return <rect key={i} x={x} y={150 - h} width={680 / n - 4} height={h} rx={4} fill={i === m - 1 ? (bad ? C.red : C.teal) : (bad ? '#F4A3AA' : '#9ED8CF')} />; })}
      </Card>{lab(v.label, 235)}</g>;
    }
    case 'growth': {
      const yrs = Math.max(1, v.years || 30); const n = 10;
      return <g>{Array.from({length: n}).map((_, i) => { const g = (Math.pow(1.08, ((i + 1) / n) * yrs) - 1) / (Math.pow(1.08, yrs) - 1); const k = ease(f, at + i * 4, at + 20 + i * 4);
        const h = 20 + 360 * g * k; const x = -330 + i * 72;
        return <rect key={i} x={x - 26} y={170 - h} width={52} height={h} rx={10} fill={i === n - 1 ? th.accent : C.teal} opacity={0.45 + 0.55 * (i + 1) / n} />; })}
        <T x={360} y={-245} size={52} fill={th.accent} anchor="start">{'سال ' + Math.round(yrs * t)}</T>{lab(v.label, 235)}</g>;
    }
    case 'flow': {
      const box = (x: number, txt: string, col: string, k: number) => <g transform={`translate(${x} 0) scale(${0.8 + 0.2 * Math.min(1, k)})`} opacity={Math.min(1, k * 1.5)}>
        <rect x={-150} y={-80} width={300} height={170} rx={28} fill="rgba(0,0,0,0.1)" /><rect x={-150} y={-90} width={300} height={170} rx={28} fill={th.card} />
        <rect x={-150} y={-90} width={300} height={22} rx={11} fill={col} />
        <foreignObject x={-140} y={-62} width={280} height={130}><div style={{width: 280, height: 130, display: 'flex', alignItems: 'center', justifyContent: 'center',
          textAlign: 'center', direction: 'rtl', fontFamily: 'F_titr', fontSize: (txt || '').length > 12 ? 36 : 46, lineHeight: 1.25, color: th.cardInk}}>{P(txt)}</div></foreignObject></g>;
      return <g>{box(230, v.from, th.sub, sp(f, at))}{box(-230, v.to, th.accent, sp(f, at + 8))}
        {[0, 1, 2, 3, 4].map((j) => { const q = ((f - at) / 28 + j / 5) % 1; if (f < at + 10 + j * 3) return null;
          return <g key={j} transform={`translate(${80 - 160 * q} ${-Math.sin(q * Math.PI) * 90})`}><circle r={18} fill={C.yellow} stroke="#C98A00" strokeWidth={4} /></g>; })}
        {v.label && <T y={190} size={56} fill={th.accent} o={ease(f, at + 12, at + 24)}>{v.label.slice(0, 30)}</T>}</g>;
    }
    case 'compare': {
      const mx = Math.max(1e-6, Math.abs(v.a.value), Math.abs(v.b.value));
      const row = (r: {label: string; value: number}, y: number, col: string, d: number) => { const k = ease(f, at + 6 + d, at + 40 + d); const w = 560 * Math.abs(r.value) / mx * k;
        return <g key={y}><T x={340} y={y - 24} size={40} fill={th.ink} anchor="start">{r.label.slice(0, 30)}</T>
          <rect x={340 - 560} y={y} width={560} height={70} rx={20} fill={th.ink} opacity={0.08} />
          <rect x={340 - w} y={y} width={w} height={70} rx={20} fill={col} />
          <text x={340 - w - 18} y={y + 54} direction="rtl" textAnchor="start" fontFamily="F_titr" fontSize={46} fill={col}>{fmt(r.value * k)}{rest(v.unit) ? ' ' + rest(v.unit) : ''}</text></g>; };
      const onHook = th.ink === C.white && th.card === C.white;     // coloured hook background: bars in white/dark so they never vanish
      return <g>{row(v.a, -120, onHook ? C.white : C.red, 0)}{row(v.b, 70, onHook ? th.accent : C.teal, 12)}</g>;
    }
    case 'meter': {
      const col = v.good ? C.teal : C.red; const val = v.from + (v.to - v.from) * t;
      return <g>{lab(v.label, -100)}<rect x={-360} y={-40} width={720} height={84} rx={42} fill={th.ink} opacity={0.08} />
        <rect x={360 - 720 * Math.max(0, Math.min(1, val))} y={-40} width={720 * Math.max(0, Math.min(1, val))} height={84} rx={42} fill={col} />
        <text y={170} textAnchor="middle" fontFamily="F_titr" fontSize={110} fill={col}>{P(Math.round(val * 100) + '%')}</text></g>;
    }
    case 'stack': {
      const val = v.from + (v.to - v.from) * t; const n = Math.round(1 + 11 * Math.max(0, Math.min(1, val)));
      return <g>{[-170, 0, 170].map((cx, s) => Array.from({length: Math.max(1, n - s * 2)}).map((_, i) =>
        <g key={s + '-' + i} transform={`translate(${cx} ${150 - i * 26})`}><ellipse rx={70} ry={20} cy={9} fill="#C98A00" /><ellipse rx={70} ry={20} fill={C.yellow} /></g>))}{lab(v.label, 235)}</g>;
    }
    case 'wave': {
      const calm = v.calm ? t : 1 - t; let d = 'M-340 40';
      for (let i = 0; i <= 68; i++) { const x = -340 + i * 10; const sk = Math.max(0, Math.sin(i * 0.55 + f / 8)) ** 8 * 200; d += ` L${x} ${40 - sk * (1 - calm) - 22 * Math.sin(i * 0.25 + f / 20)}`; }
      return <g><Card x={-380} y={-200} w={760} h={340} th={th}><path d={d} stroke={calm > 0.5 ? C.teal : C.red} strokeWidth={9} fill="none" strokeLinejoin="round" /></Card>{lab(v.label, 210)}</g>;
    }
    case 'icon': {
      const n = Math.min(8, Math.max(1, v.count || 1));
      return <g>{n === 1 ? <Badge name={v.name} x={0} y={-20} r={150} color={th.accent} k={Math.min(1, p)} cross={v.cross} /> :
        Array.from({length: n}).map((_, i) => <Badge key={i} name={v.name} x={255 - (i % 4) * 170} y={-110 + Math.floor(i / 4) * 170} r={70}
          color={i % 2 ? C.teal : th.accent} k={Math.min(1, sp(f, at + i * 3))} cross={v.cross} />)}{lab(v.label, 220)}</g>;
    }
    case 'clock': {
      const mins = (s: string) => { const m = /(\d+):(\d+)/.exec(s || ''); return m ? +m[1] * 60 + +m[2] : 0; };
      let a = mins(v.from), b = mins(v.to); if (b < a) b += 1440; const c = a + (b - a) * t;
      return <g><circle r={180} cy={10} fill="rgba(0,0,0,0.1)" /><circle r={180} fill={th.card} /><circle r={150} fill="none" stroke={th.accent} strokeWidth={10} />
        <line x2={0} y2={-85} stroke={th.cardInk} strokeWidth={14} strokeLinecap="round" transform={`rotate(${(c / 60) * 30})`} />
        <line x2={0} y2={-125} stroke={th.accent} strokeWidth={8} strokeLinecap="round" transform={`rotate(${c * 6})`} /><circle r={14} fill={th.accent} />
        <text y={262} textAnchor="middle" fontFamily="F_titr" fontSize={60} fill={th.ink}>{P(String(Math.floor(c / 60) % 24).padStart(2, '0') + ':' + String(Math.floor(c % 60)).padStart(2, '0'))}</text></g>;
    }
    case 'checklist': {
      const items = (v.items || []).slice(0, 4);
      return <g>{items.map((it, i) => { const k = sp(f, at + 4 + i * 10); const y = -((items.length - 1) * 125) / 2 + i * 125;
        return <g key={i} opacity={Math.min(1, k * 1.5)} transform={`translate(${(1 - Math.min(1, k)) * -80} 0)`}>
          <rect x={-380} y={y - 50} width={760} height={104} rx={24} fill="rgba(0,0,0,0.08)" /><rect x={-380} y={y - 56} width={760} height={104} rx={24} fill={th.card} />
          <circle cx={320} cy={y - 4} r={32} fill={v.bad ? C.red : C.teal} />
          <path d={v.bad ? `M${306} ${y - 18} L${334} ${y + 10} M${334} ${y - 18} L${306} ${y + 10}` : `M${304} ${y - 4} L${316} ${y + 8} L${338} ${y - 16}`} stroke="#fff" strokeWidth={8} fill="none" strokeLinecap="round" strokeLinejoin="round" />
          <T x={270} y={y + 12} size={46} fill={th.cardInk} anchor="start">{it.slice(0, 30)}</T></g>; })}</g>;
    }
    case 'node': return <g transform="scale(0.9) translate(0 -20)"><FlatMap focus={(v as any).name || node} label={(v as any).label} f={f} at={at} th={th} /></g>;
    case 'question': {
      const q = sp(f, at, 9, 120);
      return <g><text y={110} textAnchor="middle" fontFamily="F_titr" fontSize={380} fill={th.accent} opacity={0.18} transform={`rotate(${Math.sin(f / 10) * 6}) scale(${q})`}>؟</text>
        <foreignObject x={-390} y={-140} width={780} height={280}><div style={{width: 780, height: 280, display: 'flex', alignItems: 'center', justifyContent: 'center',
          textAlign: 'center', direction: 'rtl', fontFamily: 'F_titr', fontSize: (v.text || '').length > 40 ? 52 : 64, lineHeight: 1.4, color: th.ink, opacity: ease(f, at, at + 12)}}>{P(v.text)}</div></foreignObject></g>;
    }
    case 'versus': {
      const card = (x: number, title: string, txt: string, col: string, k: number) => <g transform={`translate(${x} 0) scale(${0.85 + 0.15 * Math.min(1, k)})`} opacity={Math.min(1, k * 1.5)}>
        <rect x={-185} y={-200} width={370} height={420} rx={30} fill="rgba(0,0,0,0.1)" /><rect x={-185} y={-210} width={370} height={420} rx={30} fill={th.card} />
        <rect x={-185} y={-210} width={370} height={96} rx={30} fill={col} /><rect x={-185} y={-140} width={370} height={26} fill={col} />
        <T y={-145} size={52} fill="#FFFFFF">{title}</T>
        <foreignObject x={-165} y={-96} width={330} height={290}><div style={{fontFamily: 'F_yekan', fontWeight: 800, fontSize: txt.length > 60 ? 34 : 42, lineHeight: 1.5,
          color: th.cardInk, textAlign: 'center', direction: 'rtl'}}>{P(txt)}</div></foreignObject></g>;
      return <g>{card(200, 'باور غلط', v.myth || '', C.red, sp(f, at))}{card(-200, 'واقعیت', v.fact || '', C.teal, sp(f, at + 24))}</g>;
    }
  }
  return null;
};

const Wipe: React.FC<{f: number; at: number; color: string; W: number; H: number; right: boolean}> = ({f, at, color, W, H, right}) => {
  const k = ease(f, at, at + 14);
  return k > 0 && k < 1 ? <svg width={W} height={H} style={{position: 'absolute'}}><circle cx={right ? W * 0.85 : W * 0.15} cy={H * 0.2} r={k * Math.hypot(W, H)} fill={color} /></svg> : null;
};

const Cover: React.FC<{text: string; f: number; bg?: string; hi?: string}> = ({text, f, bg = C.orange, hi = C.navy}) => {
  const o = interpolate(f, [62, 76], [1, 0], cl); if (o <= 0) return null;
  const ws = text.split(/\s+/).filter(Boolean).slice(0, 6);
  const size = text.length > 22 ? 118 : 140;
  return <AbsoluteFill style={{background: bg, opacity: o}}>
    <div style={{position: 'absolute', top: 470, left: 60, right: 60, display: 'flex', flexWrap: 'wrap', justifyContent: 'center', direction: 'rtl', columnGap: 22}}>
      {ws.map((w, i) => <span key={i} style={{position: 'relative', fontFamily: 'F_lalezar', fontSize: size, lineHeight: 1.4, color: i === ws.length - 1 ? hi : C.white}}>
        {i === ws.length - 1 && <span style={{position: 'absolute', right: -8, left: -8, bottom: size * 0.2, height: size * 0.42, background: C.yellow, borderRadius: 14, zIndex: -1}} />}
        <span style={{position: 'relative'}}>{P(w)}</span></span>)}
    </div>
  </AbsoluteFill>;
};

export const FaEpisode: React.FC<TLEpProps> = ({beats, vertical, cover, brand = 'پول و قدرت', palette = 0}) => {
  const PAL = PALETTES[Math.abs(palette) % PALETTES.length]; const THEMES = PAL.slice(0, 3); const HOOK = PAL[3];
  const f = useCurrentFrame();
  const W = vertical ? 1080 : 1920, H = vertical ? 1920 : 1080;
  let i = beats.findIndex((b) => f >= b.start && f < b.end); if (i < 0) i = f < (beats[0]?.start || 0) ? 0 : beats.length - 1;
  const b = beats[i]; if (!b) return <AbsoluteFill style={{background: C.cream}} />;
  // sections: a new section starts where the stage changes; the hook (before the first stage) is orange
  const secStart: number[] = []; let sec = -1;
  for (let q = 0; q <= i; q++) if (q === 0 || beats[q].stage !== beats[q - 1].stage) { sec++; secStart.push(beats[q].start); }
  const hook = !b.stage && i < 8 && beats.slice(0, i + 1).every((x) => !x.stage);
  const themeFor = (k: number) => (k === 0 && !beats[0].stage ? HOOK : THEMES[k % THEMES.length]);
  const th = hook ? HOOK : themeFor(sec);
  const prevTh = sec > 0 ? themeFor(sec - 1) : th;
  const sAt = secStart[secStart.length - 1];
  const dur = b.end - b.start;
  const out = interpolate(f, [b.end - 6, b.end], [1, 0], cl);
  const textOnly = b.visual?.type === 'question';
  const L = vertical ? {words: [60, 420, 960, 96], wc: [540, 1080], ws: 1.32, stamp: [W - 60, 150]} : {words: [120, 60, 1680, 96], wc: [960, 650], ws: 1.25, stamp: [W - 70, 70]};
  return <AbsoluteFill style={{background: f < sAt + 14 ? prevTh.bg : th.bg}}>
    <Wipe f={f} at={sAt} color={th.bg} W={W} H={H} right={sec % 2 === 0} />
    {f >= sAt + 14 && <AbsoluteFill style={{background: th.bg}} />}
    {/* section label (stage) */}
    {b.stage && <div style={{position: 'absolute', top: L.stamp[1], right: W - L.stamp[0], direction: 'rtl', opacity: ease(f, sAt + 8, sAt + 18),
      transform: `translateY(${(1 - ease(f, sAt + 8, sAt + 18)) * -30}px)`, background: th.accent, color: th.bg === C.navy ? C.navy : C.white,
      fontFamily: 'F_lalezar', fontSize: vertical ? 50 : 44, padding: '4px 28px', borderRadius: 40}}>{P(b.stage)}</div>}
    <div style={{position: 'absolute', top: vertical ? 70 : 34, left: vertical ? 60 : 56, direction: 'rtl', fontFamily: 'F_yekan', fontSize: vertical ? 34 : 28,
      color: th.sub, display: 'flex', alignItems: 'center', gap: 12, opacity: vertical ? 0 : 1}}>
      <span style={{width: 16, height: 16, borderRadius: 8, background: th.accent, display: 'inline-block'}} />{brand}</div>
    <div key={'w' + i} style={{opacity: out}}>
      {!textOnly && <KWords words={b.words || []} f={f} at={b.start + 2} size={L.words[3]} th={th} top={L.words[1] + (vertical ? 0 : 40)} width={L.words[2]} left={L.words[0]} />}
    </div>
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position: 'absolute'}}>
      <g key={'v' + i} opacity={Math.min(ease(f, b.start, b.start + 6), out)}
        transform={`translate(${L.wc[0]} ${textOnly ? H / 2 : L.wc[1]}) scale(${(textOnly ? 1.25 : L.ws) * (0.94 + 0.06 * Math.min(1, sp(f, b.start)))})`}>
        <Widget v={b.visual} f={f} at={b.start + 6} dur={dur} th={th} node={b.node} />
      </g>
    </svg>
    {vertical && cover && f < 80 && <Cover text={cover} f={f} bg={HOOK.bg} hi={HOOK.accent} />}
  </AbsoluteFill>;
};

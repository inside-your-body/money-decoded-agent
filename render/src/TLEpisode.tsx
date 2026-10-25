// Money Decoded format (owner approved, Oct 24 2026): a money story told on a timeline.
// Dark navy + mint hologram MONEY MAP (the place we talk about lights up, coins travel to it), yellow time stamps, a timeline bar,
// one code-drawn widget per sentence, kinetic key words. Everything is code — deterministic layout, nothing overlaps.
// Long = 1920x1080, Short = 1080x1920.
import React from 'react';
import {AbsoluteFill, useCurrentFrame, spring, interpolate} from 'remotion';
import {MoneyMap, MoneyNode, NODES} from './MoneyMap';
import {TL, BigStamp, Words, TimeBar} from './Timeline';
import {ICONS, iconPath} from './Icons';
import './theme';

const cl = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};
const sp = (f: number, at: number, d = 13, s = 170) => Math.min(1.08, spring({frame: f - at, fps: 30, config: {damping: d, stiffness: s}}));
const GOOD = '#2EE6A6', BAD = '#FF5A4E', GOLD = '#FFD23F';

export type Visual =
  | {type: 'stat'; value: number; prefix?: string; unit?: string; label: string; good?: boolean}
  | {type: 'chart'; shape: 'rise' | 'fall' | 'crash' | 'bubble' | 'recover' | 'zigzag' | 'flat'; label?: string}
  | {type: 'growth'; years: number; label?: string}
  | {type: 'flow'; from: string; to: string; label?: string}
  | {type: 'meter'; label: string; from: number; to: number; good?: boolean}
  | {type: 'stack'; from: number; to: number; label?: string}
  | {type: 'wave'; label: string; calm: boolean}
  | {type: 'compare'; a: {label: string; value: number}; b: {label: string; value: number}; unit?: string}
  | {type: 'icon'; name: string; cross?: boolean; count?: number; label?: string}
  | {type: 'clock'; from: string; to: string}
  | {type: 'checklist'; items: string[]; bad?: boolean}
  | {type: 'node'; name: string; state?: 'glow' | 'grow' | 'shrink' | 'crack' | 'frozen'; label?: string}
  | {type: 'question'; text: string}
  | {type: 'versus'; myth: string; fact: string};

export type TLBeat = {start: number; end: number; stage: string | null; stageIdx: number; node: string; visual: Visual; words: string[]};
export type TLEpProps = {beats: TLBeat[]; marks: string[]; frames: number; vertical?: boolean; title?: string};

const Label: React.FC<{y: number; text?: string; o?: number}> = ({y, text, o = 1}) => text ?
  <text x={0} y={y} textAnchor="middle" fontFamily="F_inter" fontWeight={800} fontSize={28} letterSpacing={5} fill={TL.mute} opacity={o}>{text.toUpperCase().slice(0, 34)}</text> : null;

const fmt = (v: number) => (Math.abs(v) >= 1000 ? Math.round(v).toLocaleString('en-US') : (Math.abs(v) < 10 && v % 1 ? v.toFixed(1) : String(Math.round(v))));

// price-line shapes (x 0..1 -> y 0..1, 1 = top)
const SHAPES: Record<string, (x: number) => number> = {
  rise: (x) => 0.12 + 0.72 * x + 0.06 * Math.sin(x * 19),
  fall: (x) => 0.85 - 0.7 * x + 0.05 * Math.sin(x * 17),
  crash: (x) => x < 0.6 ? 0.55 + 0.35 * x + 0.04 * Math.sin(x * 23) : 0.76 - 0.66 * Math.min(1, (x - 0.6) / 0.18) + 0.03 * Math.sin(x * 30),
  bubble: (x) => x < 0.7 ? 0.12 + 0.8 * Math.pow(x / 0.7, 3) : 0.92 - 0.82 * Math.min(1, (x - 0.7) / 0.15),
  recover: (x) => x < 0.35 ? 0.75 - 1.6 * x : 0.19 + 0.75 * (x - 0.35) / 0.65 + 0.04 * Math.sin(x * 21),
  zigzag: (x) => 0.5 + 0.3 * Math.sin(x * 14) * (0.6 + 0.4 * Math.sin(x * 5)),
  flat: (x) => 0.5 + 0.03 * Math.sin(x * 25),
};

// every widget draws inside a ±380 x ±230 box around (0,0)
const Widget: React.FC<{v: Visual; f: number; at: number; dur: number}> = ({v, f, at, dur}) => {
  const p = sp(f, at), t = interpolate(f, [at + 6, at + Math.min(70, dur * 0.7)], [0, 1], {...cl, easing: (x) => 1 - Math.pow(1 - x, 3)});
  const pulse = 0.5 + 0.5 * Math.sin(f / 6);
  switch (v.type) {
    case 'chart': {
      const fn = SHAPES[v.shape] || SHAPES.zigzag; const n = 90; const draw = Math.max(0.02, t);
      const pts = Array.from({length: Math.round(n * draw) + 1}).map((_, i) => { const x = i / n; return [-340 + 680 * x, 170 - 340 * fn(x)]; });
      const last = pts[pts.length - 1]; const up = pts.length > 3 && last[1] <= pts[Math.max(0, pts.length - 8)][1];
      const col = v.shape === 'rise' || v.shape === 'recover' ? GOOD : v.shape === 'flat' || v.shape === 'zigzag' ? GOLD : (up ? GOOD : BAD);
      const d = 'M' + pts.map((q) => q.map((z) => z.toFixed(1)).join(' ')).join(' L');
      return <g opacity={Math.min(1, p * 1.5)}>
        <rect x={-370} y={-200} width={740} height={400} rx={24} fill={TL.bg2} opacity={0.65} />
        {[-120, -40, 40, 120].map((y) => <line key={y} x1={-350} x2={350} y1={y} y2={y} stroke={TL.mute} strokeOpacity={0.22} />)}
        <path d={d + ` L${last[0]} 190 L-340 190 Z`} fill={col} opacity={0.12} />
        <path d={d} stroke={col} strokeWidth={8} fill="none" strokeLinejoin="round" strokeLinecap="round" />
        <circle cx={last[0]} cy={last[1]} r={13 + 4 * pulse} fill={col} />
        <Label y={250} text={v.label} />
      </g>;
    }
    case 'growth': {
      const yrs = Math.max(1, v.years || 30); const n = 60; const draw = Math.max(0.02, t);
      const g = (x: number) => (Math.pow(1.07, x * yrs) - 1) / (Math.pow(1.07, yrs) - 1);
      const pts = Array.from({length: Math.round(n * draw) + 1}).map((_, i) => { const x = i / n; return [-330 + 640 * x, 170 - 330 * g(x)]; });
      const d = 'M' + pts.map((q) => q.map((z) => z.toFixed(1)).join(' ')).join(' L');
      const last = pts[pts.length - 1];
      return <g opacity={Math.min(1, p * 1.5)}>
        <line x1={-340} y1={180} x2={340} y2={180} stroke={TL.mute} strokeWidth={4} />
        <line x1={-340} y1={180} x2={-340} y2={-190} stroke={TL.mute} strokeWidth={4} />
        <line x1={-330} y1={170} x2={-330 + 640 * draw} y2={170 - 330 * draw * 0.35} stroke={TL.mute} strokeWidth={4} strokeDasharray="10 12" />
        <path d={d} stroke={GOOD} strokeWidth={9} fill="none" strokeLinecap="round" />
        <circle cx={last[0]} cy={last[1]} r={14 + 4 * pulse} fill={GOLD} />
        <text x={330} y={225} textAnchor="end" fontFamily="F_anton" fontSize={44} fill={GOLD}>YEAR {Math.round(yrs * draw)}</text>
        <Label y={260} text={v.label} />
      </g>;
    }
    case 'flow': {
      const box = (x: number, txt: string, col: string) => <g transform={`translate(${x} 0)`}>
        <rect x={-130} y={-70} width={260} height={140} rx={22} fill={TL.bg2} stroke={col} strokeWidth={5} />
        <foreignObject x={-122} y={-62} width={244} height={124}>
          <div style={{width: 244, height: 124, display: 'flex', alignItems: 'center', justifyContent: 'center', textAlign: 'center',
            fontFamily: 'F_anton', fontSize: (txt || '').length > 10 ? 38 : 50, lineHeight: 1.05, color: TL.ink}}>{(txt || '').toUpperCase()}</div>
        </foreignObject>
      </g>;
      return <g opacity={Math.min(1, p * 1.5)}>
        {box(-235, v.from, TL.mute)}{box(235, v.to, GOOD)}
        <line x1={-100} y1={0} x2={100} y2={0} stroke={TL.mute} strokeWidth={4} strokeDasharray="8 10" />
        {[0, 1, 2, 3, 4, 5].map((j) => {
          const q = ((f - at) / 26 + j / 6) % 1; if (f < at + j * 3) return null;
          const x = -95 + 190 * q, y = -Math.sin(q * Math.PI) * 70;
          return <g key={j} transform={`translate(${x} ${y})`} opacity={Math.sin(q * Math.PI)}>
            <circle r={18} fill={GOLD} stroke="#FFF3B0" strokeWidth={3} />
            <text y={8} textAnchor="middle" fontFamily="F_anton" fontSize={24} fill={TL.bg}>$</text></g>;
        })}
        {v.label && <text y={175} textAnchor="middle" fontFamily="F_anton" fontSize={64} fill={GOLD}>{v.label.toUpperCase().slice(0, 24)}</text>}
      </g>;
    }
    case 'stack': {
      const val = v.from + (v.to - v.from) * t; const n = Math.round(1 + 13 * Math.max(0, Math.min(1, val)));
      const col = v.to >= v.from ? GOLD : '#E0A21A';
      return <g opacity={Math.min(1, p * 1.5)}>
        {[-150, 0, 150].map((cx, s) => Array.from({length: Math.max(1, n - s * 2)}).map((_, i) =>
          <g key={s + '-' + i} transform={`translate(${cx} ${180 - i * 24})`}>
            <ellipse rx={62} ry={18} cy={8} fill="#B8860B" />
            <ellipse rx={62} ry={18} fill={col} stroke="#FFF3B0" strokeWidth={2} />
          </g>))}
        <Label y={250} text={v.label} />
      </g>;
    }
    case 'node': {
      const key = (v.name in NODES ? v.name : 'bank') as keyof typeof NODES;
      const nd = v.name === 'you' ? {label: 'YOU', icon: 'person', c: GOOD} : NODES[key];
      const st = v.state || 'glow';
      const sc = st === 'grow' ? 0.8 + 0.4 * t : st === 'shrink' ? 1.15 - 0.45 * t : 1;
      const col = st === 'crack' ? BAD : st === 'frozen' ? '#9FD8FF' : nd.c;
      return <g opacity={Math.min(1, p * 1.5)}>
        <circle r={200 + 14 * pulse} fill={col} opacity={0.08} />
        <circle r={190} fill={TL.bg2} stroke={col} strokeWidth={7} />
        <g transform={`scale(${2.6 * sc * (0.9 + 0.1 * p)}) translate(-50 -50)`}>
          <path d={iconPath(nd.icon)} fill="none" stroke={col} strokeWidth={4.5} strokeLinecap="round" strokeLinejoin="round" />
        </g>
        {st === 'crack' && <path d={`M-40 -190 L-10 -90 L-50 -20 L10 60 L-20 190`} fill="none" stroke={BAD} strokeWidth={9} pathLength={1}
          strokeDasharray={`${t} 1`} strokeLinecap="round" />}
        {st === 'frozen' && [0, 1, 2, 3, 4, 5].map((i) => <line key={i} x1={0} y1={-215} x2={0} y2={-180} stroke="#9FD8FF" strokeWidth={6}
          transform={`rotate(${i * 60})`} opacity={t} />)}
        <Label y={260} text={v.label || nd.label} />
      </g>;
    }
    case 'stat': {
      const col = v.good === false ? BAD : v.good ? GOOD : GOLD;
      const val = fmt((v.value || 0) * t);
      return <g opacity={Math.min(1, p * 1.5)}><Label y={275} text={v.label} /><g transform={`scale(${0.7 + 0.3 * p})`}>
        <circle r={210} fill="none" stroke={col} strokeOpacity={0.15} strokeWidth={30} />
        <circle r={210} fill="none" stroke={col} strokeWidth={6} pathLength={1} strokeDasharray={`${t} 1`} transform="rotate(-90)" strokeLinecap="round" />
        <text y={40} textAnchor="middle" fontFamily="F_anton" fontSize={((n) => n > 9 ? 78 : n > 7 ? 96 : n > 5 ? 124 : 150)((v.prefix || '').length + val.length + (v.unit || '').length)} fill={col}>
          {v.prefix || ''}{val}<tspan fontSize={60} dx={8}>{v.unit || ''}</tspan></text>
      </g></g>;
    }
    case 'meter': {
      const col = v.good ? GOOD : BAD; const val = v.from + (v.to - v.from) * t;
      return <g opacity={Math.min(1, p * 1.5)}>
        <Label y={-80} text={v.label} />
        <rect x={-340} y={-40} width={680} height={80} rx={40} fill={TL.bg2} stroke={TL.mute} strokeWidth={3} />
        <rect x={-332} y={-32} width={Math.max(0, 664 * Math.min(1, Math.max(0, val)))} height={64} rx={32} fill={col} />
        {[0.25, 0.5, 0.75].map((k) => <line key={k} x1={-340 + 680 * k} x2={-340 + 680 * k} y1={50} y2={66} stroke={TL.mute} strokeWidth={3} />)}
        <text y={150} textAnchor="middle" fontFamily="F_anton" fontSize={90} fill={col}>{Math.round(val * 100)}%</text>
      </g>;
    }
    case 'wave': {
      const calm = v.calm ? t : 1 - t;
      let d = 'M-340 40';
      for (let i = 0; i <= 68; i++) {
        const x = -340 + i * 10; const spike = Math.max(0, Math.sin(i * 0.55 + f / 8)) ** 8 * 200;
        d += ` L${x} ${40 - spike * (1 - calm) - 26 * Math.sin(i * 0.25 + f / 20)}`;
      }
      return <g opacity={Math.min(1, p * 1.5)}>
        <rect x={-370} y={-200} width={740} height={320} rx={24} fill={TL.bg2} opacity={0.6} />
        {[-140, -60, 20, 100].map((y) => <line key={y} x1={-350} x2={350} y1={y} y2={y} stroke={TL.mute} strokeOpacity={0.25} />)}
        <path d={d} stroke={calm > 0.5 ? GOOD : BAD} strokeWidth={7} fill="none" strokeLinejoin="round" />
        <Label y={180} text={v.label} />
      </g>;
    }
    case 'compare': {
      const mx = Math.max(1e-6, Math.abs(v.a.value), Math.abs(v.b.value));
      const row = (r: {label: string; value: number}, y: number, col: string, d: number) => {
        const k = interpolate(f, [at + 8 + d, at + 50 + d], [0, 1], cl);
        return <g key={y}>
          <text x={-340} y={y - 22} fontFamily="F_inter" fontWeight={800} fontSize={38} letterSpacing={3} fill={TL.ink}>{r.label.toUpperCase().slice(0, 26)}</text>
          <rect x={-340} y={y} width={520 * Math.abs(r.value) / mx * k} height={60} rx={12} fill={col} />
          <text x={-340 + 520 * Math.abs(r.value) / mx * k + 20} y={y + 48} fontFamily="F_anton" fontSize={52} fill={col}>{fmt(r.value * k)}{v.unit || ''}</text>
        </g>;
      };
      return <g opacity={Math.min(1, p * 1.5)}>{row(v.a, -110, BAD, 0)}{row(v.b, 70, GOOD, 14)}</g>;
    }
    case 'icon': {
      const n = Math.min(8, Math.max(1, v.count || 1));
      const one = (x: number, y: number, s: number, k: number, key: number) =>
        <g key={key} transform={`translate(${x} ${y}) scale(${s * k}) translate(-50 -50)`}>
          <path d={iconPath(v.name)} fill="none" stroke={GOLD} strokeWidth={14 / s} opacity={0.18} strokeLinecap="round" strokeLinejoin="round" />
          <path d={iconPath(v.name)} fill="none" stroke={v.cross ? TL.ink : GOLD} strokeWidth={5 / Math.max(1, s / 3)} strokeLinecap="round" strokeLinejoin="round"
            pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - Math.min(1, k)} />
        </g>;
      return <g>
        <circle r={190 + 6 * pulse} fill={GOLD} opacity={0.06} />
        <circle r={190} fill="none" stroke={GOLD} strokeOpacity={0.35} strokeWidth={3} strokeDasharray="4 12" transform={`rotate(${f})`} />
        {n === 1 ? one(0, -10, 3.2, p, 0) :
          Array.from({length: n}).map((_, i) => one(-255 + (i % 4) * 170, -130 + Math.floor(i / 4) * 140, 0.95, sp(f, at + i * 4), i))}
        {v.cross && <g opacity={sp(f, at + 18)} stroke={BAD} strokeWidth={22} strokeLinecap="round">
          <line x1={-150} y1={-150} x2={-150 + 300 * sp(f, at + 18)} y2={-150 + 300 * sp(f, at + 18)} />
          <line x1={150} y1={-150} x2={150 - 300 * sp(f, at + 24)} y2={-150 + 300 * sp(f, at + 24)} /></g>}
        <Label y={230} text={v.label} />
      </g>;
    }
    case 'clock': {
      const mins = (s: string) => { const m = /(\d+):(\d+)/.exec(s || ''); return m ? +m[1] * 60 + +m[2] : 0; };
      let a = mins(v.from), b = mins(v.to); if (b < a) b += 24 * 60;
      const cur = a + (b - a) * t; const h = Math.floor(cur / 60) % 24, m = Math.floor(cur % 60);
      return <g opacity={Math.min(1, p * 1.5)}>
        <circle r={170} fill={TL.bg2} stroke={GOOD} strokeWidth={6} />
        {Array.from({length: 12}).map((_, i) => <line key={i} x1={0} y1={-150} x2={0} y2={-130} stroke={TL.ink} strokeWidth={5} transform={`rotate(${i * 30})`} />)}
        <line x1={0} y1={0} x2={0} y2={-90} stroke={TL.ink} strokeWidth={10} strokeLinecap="round" transform={`rotate(${(cur / 60) * 30})`} />
        <line x1={0} y1={0} x2={0} y2={-130} stroke={GOLD} strokeWidth={6} strokeLinecap="round" transform={`rotate(${cur * 6})`} />
        <circle r={10} fill={GOLD} />
        <text x={0} y={250} textAnchor="middle" fontFamily="F_anton" fontSize={60} fill={GOLD}>{String(h).padStart(2, '0')}:{String(m).padStart(2, '0')}</text>
      </g>;
    }
    case 'checklist': {
      const items = (v.items || []).slice(0, 4);
      return <g>{items.map((it, i) => {
        const k = sp(f, at + 6 + i * 12); const y = -((items.length - 1) * 130) / 2 + i * 130;
        return <g key={i} opacity={Math.min(1, k * 1.5)} transform={`translate(${(1 - Math.min(1, k)) * 80} 0)`}>
          <rect x={-370} y={y - 56} width={740} height={112} rx={20} fill={TL.bg2} stroke={v.bad ? BAD : GOOD} strokeOpacity={0.5} strokeWidth={3} />
          <g transform={`translate(-310 ${y}) scale(0.5) translate(-50 -50)`}>
            <path d={v.bad ? ICONS.cross : ICONS.check} fill="none" stroke={v.bad ? BAD : GOOD} strokeWidth={14} strokeLinecap="round" strokeLinejoin="round" /></g>
          <text x={-240} y={y + 20} fontFamily="F_inter" fontWeight={800} fontSize={54} fill={TL.ink}>{it.slice(0, 26)}</text>
        </g>;
      })}</g>;
    }
    case 'question':
      return <g opacity={Math.min(1, p * 1.5)} transform={`scale(${0.8 + 0.2 * p})`}>
        <text y={60} textAnchor="middle" fontFamily="F_anton" fontSize={300} fill={GOLD} opacity={0.15} transform={`rotate(${Math.sin(f / 15) * 6})`}>?</text>
        <foreignObject x={-360} y={-120} width={720} height={240}>
          <div style={{width: 720, height: 240, display: 'flex', alignItems: 'center', justifyContent: 'center', textAlign: 'center',
            fontFamily: 'F_anton', fontSize: (v.text || '').length > 40 ? 52 : 66, lineHeight: 1.1, color: TL.ink}}>{v.text}</div>
        </foreignObject>
      </g>;
    case 'versus': {
      const k2 = sp(f, at + 25);
      const card = (x: number, title: string, txt: string, col: string, k: number) =>
        <g transform={`translate(${x} 0) scale(${0.85 + 0.15 * Math.min(1, k)})`} opacity={Math.min(1, k * 1.5)}>
          <rect x={-185} y={-210} width={370} height={420} rx={24} fill={TL.bg2} stroke={col} strokeWidth={4} />
          <text y={-120} textAnchor="middle" fontFamily="F_anton" fontSize={64} fill={col}>{title}</text>
          <foreignObject x={-165} y={-90} width={330} height={290}>
            <div style={{fontFamily: 'F_inter', fontWeight: 800, fontSize: txt.length > 60 ? 36 : 44, lineHeight: 1.2, color: TL.ink, textAlign: 'center'}}>{txt}</div>
          </foreignObject>
        </g>;
      return <g>{card(-195, 'MYTH', v.myth || '', BAD, p)}{card(195, 'FACT', v.fact || '', GOOD, k2)}</g>;
    }
  }
  return null;
};

const NODE_OK = new Set(['you', 'bank', 'market', 'central_bank', 'government', 'company', 'home', 'debt', 'gold', 'none']);
const normNode = (o: string): MoneyNode => (NODE_OK.has(o) ? o : 'none') as MoneyNode;

export const TLEpisode: React.FC<TLEpProps> = ({beats, marks, vertical}) => {
  const f = useCurrentFrame();
  let i = beats.findIndex((b) => f >= b.start && f < b.end); if (i < 0) i = f < (beats[0]?.start || 0) ? 0 : beats.length - 1;
  const b = beats[i]; if (!b) return <AbsoluteFill style={{background: TL.bg}} />;
  // the node glow and the stamp only restart when they actually change; coins travel from the previous node
  let nodeAt = b.start, j = i; for (; j > 0 && normNode(beats[j - 1].node) === normNode(b.node); j--) nodeAt = beats[j - 1].start;
  let prev: MoneyNode = 'you'; for (let q = j - 1; q >= 0; q--) { const n = normNode(beats[q].node); if (n !== 'none') { prev = n; break; } }
  let stAt = b.start; for (let q = i; q > 0 && beats[q - 1].stage === b.stage; q--) stAt = beats[q - 1].start;
  const out = interpolate(f, [b.end - 6, b.end], [1, 0], cl);
  const dur = b.end - b.start;
  const W = vertical ? 1080 : 1920, H = vertical ? 1920 : 1080;
  const mapOn = interpolate(f, [0, 20], [0, 1], cl);
  const hasMarks = marks.length > 1 && b.stageIdx >= 0;
  const L = vertical
    ? {map: [540, 800, 0.95], stamp: [80, 210, 120], wid: [540, 1360, 0.8], words: [80, b.stage ? 330 : 250, 76, 920]}
    : {map: [470, 520, 0.98], stamp: [990, 200, 150], wid: [1350, b.stage ? 500 : 430, 0.92], words: [990, b.stage ? 830 : 800, 70, 860]};
  return <AbsoluteFill style={{background: `radial-gradient(circle at ${vertical ? '50% 40%' : '26% 50%'}, #14304F 0%, ${TL.bg} 68%)`}}>
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`}>
      {Array.from({length: Math.ceil(W / 120)}).map((_, k) => <line key={k} x1={k * 120} y1={0} x2={k * 120} y2={H} stroke="#FFFFFF" opacity={0.025} />)}
      {Array.from({length: 18}).map((_, k) => <circle key={'p' + k} cx={(k * 211 + f * (0.3 + (k % 3) * 0.2)) % W} cy={(k * 97) % H + Math.sin(f / 40 + k) * 20}
        r={2 + (k % 3)} fill={TL.line} opacity={0.12} />)}
      <g opacity={mapOn}><MoneyMap x={L.map[0]} y={L.map[1]} s={L.map[2]} focus={normNode(b.node)} from={prev} f={f} at={nodeAt} /></g>
      {b.stage && <BigStamp key={b.stage} text={b.stage} at={stAt} f={f} x={L.stamp[0]} y={L.stamp[1]} size={L.stamp[2]} />}
      <g key={i} opacity={out} transform={`translate(${L.wid[0]} ${L.wid[1]}) scale(${L.wid[2]})`}>
        <Widget v={b.visual} f={f} at={b.start + 2} dur={dur} />
      </g>
      <g opacity={out}><Words key={'w' + i} words={(b.words || []).slice(0, 4).map((w) => w.toUpperCase())} at={b.start + 10} f={f}
        x={L.words[0]} y={L.words[1]} size={L.words[2]} maxW={L.words[3]} /></g>
      {!vertical && hasMarks && <TimeBar marks={marks} active={b.stageIdx} f={f} at={stAt} />}
      {!vertical && <text x={60} y={66} fontFamily="F_inter" fontWeight={800} fontSize={22} letterSpacing={6} fill={TL.mute}>MONEY DECODED</text>}
    </svg>
  </AbsoluteFill>;
};
export const tlMeta = ({props}: {props: TLEpProps}) => ({durationInFrames: Math.max(30, props.frames || 300)});

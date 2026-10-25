// Signature element of Money Decoded: a glowing hologram MONEY MAP that is always on screen.
// YOU sit in the centre; 8 places of the money system sit on a ring around you. The place the narrator talks about lights up
// and coins visibly travel to it from the previous place. Local coordinates: about ±400 x ±420, centred on (0,0).
import React from 'react';
import {spring, interpolate} from 'remotion';
import {TL} from './Timeline';
import {ICONS} from './Icons';

export type MoneyNode = 'you' | 'bank' | 'market' | 'central_bank' | 'government' | 'company' | 'home' | 'debt' | 'gold' | 'none';
const cl = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};
const sp = (f: number, at: number, d = 14, s = 120) => spring({frame: f - at, fps: 30, config: {damping: d, stiffness: s}});

const R = 300;
type N = {label: string; icon: string; a: number; c: string};
export const NODES: Record<Exclude<MoneyNode, 'you' | 'none'>, N> = {
  central_bank: {label: 'CENTRAL BANK', icon: 'vault', a: -90, c: '#FFD23F'},
  bank: {label: 'BANK', icon: 'bank', a: -45, c: '#2EE6A6'},
  market: {label: 'MARKET', icon: 'chartup', a: 0, c: '#5CC8FF'},
  company: {label: 'COMPANY', icon: 'factory', a: 45, c: '#B79CFF'},
  home: {label: 'HOME', icon: 'house', a: 90, c: '#FF9F5A'},
  debt: {label: 'DEBT', icon: 'card', a: 135, c: '#FF5A6E'},
  government: {label: 'GOVERNMENT', icon: 'capitol', a: 180, c: '#7FA8FF'},
  gold: {label: 'GOLD', icon: 'gold', a: -135, c: '#FFC34D'},
};
export const nodePos = (n: MoneyNode): [number, number] => {
  if (n === 'you' || n === 'none' || !(n in NODES)) return [0, 0];
  const a = (NODES[n as keyof typeof NODES].a * Math.PI) / 180;
  return [Math.cos(a) * R, Math.sin(a) * R];
};

const Glyph: React.FC<{name: string; x: number; y: number; s: number; color: string; w?: number}> = ({name, x, y, s, color, w = 6}) =>
  <g transform={`translate(${x} ${y}) scale(${s}) translate(-50 -50)`}>
    <path d={ICONS[name] || ICONS.coin} fill="none" stroke={color} strokeWidth={w / s} strokeLinecap="round" strokeLinejoin="round" />
  </g>;

export const MoneyMap: React.FC<{x: number; y: number; s: number; focus: MoneyNode; from: MoneyNode; f: number; at: number}> = ({x, y, s, focus, from, f, at}) => {
  const k = sp(f, at);
  const pulse = 0.5 + 0.5 * Math.sin(f / 7);
  const names = Object.keys(NODES) as (keyof typeof NODES)[];
  const [fx, fy] = nodePos(from);
  const [tx, ty] = nodePos(focus);
  const travel = from !== focus && focus !== 'none';
  const youOn = focus === 'you';
  return <g transform={`translate(${x} ${y}) scale(${s})`}>
    {/* outer hologram rings */}
    <circle r={R + 92} fill="none" stroke={TL.line} strokeOpacity={0.08} strokeWidth={2} />
    <circle r={R} fill="none" stroke={TL.line} strokeOpacity={0.22} strokeWidth={3} strokeDasharray="6 14" transform={`rotate(${f * 0.15})`} />
    <circle r={R - 150} fill="none" stroke={TL.line} strokeOpacity={0.1} strokeWidth={2} />
    {/* spokes + ambient money flow */}
    {names.map((n, i) => {
      const [nx, ny] = nodePos(n); const on = n === focus;
      return <g key={n}>
        <line x1={0} y1={0} x2={nx} y2={ny} stroke={on ? NODES[n].c : TL.mute} strokeOpacity={on ? 0.75 : 0.25} strokeWidth={on ? 5 : 2.5} />
        {[0, 1, 2].map((j) => {
          const t = ((f / (on ? 40 : 90) + j / 3 + i * 0.13) % 1);
          const dir = on ? t : 1 - t;
          return <circle key={j} cx={nx * dir} cy={ny * dir} r={on ? 7 : 4} fill={on ? NODES[n].c : TL.line} opacity={on ? 0.9 : 0.25} />;
        })}
      </g>;
    })}
    {/* coins travelling from the previous place to the new one */}
    {travel && [0, 1, 2, 3, 4].map((j) => {
      const t = interpolate(f, [at + j * 4, at + 34 + j * 4], [0, 1], {...cl, easing: (v) => v * v * (3 - 2 * v)});
      if (t <= 0 || t >= 1) return null;
      const cx = fx + (tx - fx) * t, cy = fy + (ty - fy) * t - Math.sin(t * Math.PI) * 70;
      return <g key={j} transform={`translate(${cx} ${cy})`}>
        <circle r={15} fill={TL.gold} stroke="#FFF3B0" strokeWidth={3} />
        <text y={7} textAnchor="middle" fontFamily="F_anton" fontSize={20} fill={TL.bg}>$</text>
      </g>;
    })}
    {/* the 8 places */}
    {names.map((n) => {
      const nd = NODES[n]; const [nx, ny] = nodePos(n); const on = n === focus;
      const g = on ? k : 0; const r = 52 + 14 * g;
      const ly = ny >= 0 ? ny + r + 34 : ny - r - 16;
      return <g key={n}>
        {on && <circle cx={nx} cy={ny} r={r + 26 + 10 * pulse} fill={nd.c} opacity={0.16 * g} />}
        <circle cx={nx} cy={ny} r={r} fill={on ? nd.c : TL.bg2} fillOpacity={on ? 0.22 + 0.1 * pulse : 0.9}
          stroke={on ? nd.c : TL.mute} strokeWidth={on ? 6 : 3} />
        <Glyph name={nd.icon} x={nx} y={ny} s={on ? 0.62 + 0.12 * g : 0.6} color={on ? '#FFFFFF' : TL.mute} w={on ? 7 : 5} />
        <text x={nx} y={ly} textAnchor="middle" fontFamily="F_inter" fontWeight={800} fontSize={on ? 30 : 24} letterSpacing={3}
          fill={on ? nd.c : TL.mute} opacity={on ? 1 : 0.85}>{nd.label}</text>
      </g>;
    })}
    {/* YOU in the centre */}
    <circle r={84 + (youOn ? 12 * k + 6 * pulse : 0)} fill={youOn ? TL.line : TL.bg2} fillOpacity={youOn ? 0.25 : 0.95}
      stroke={youOn ? TL.line : TL.line} strokeOpacity={youOn ? 1 : 0.55} strokeWidth={youOn ? 7 : 4} />
    <circle r={100 + 8 * pulse} fill="none" stroke={TL.line} strokeOpacity={youOn ? 0.35 : 0.12} strokeWidth={3} />
    <Glyph name="person" x={0} y={-8} s={youOn ? 0.95 : 0.85} color={youOn ? '#FFFFFF' : TL.line} w={youOn ? 8 : 6} />
    <text y={60} textAnchor="middle" fontFamily="F_inter" fontWeight={800} fontSize={22} letterSpacing={4} fill={youOn ? '#FFFFFF' : TL.line}>YOU</text>
  </g>;
};

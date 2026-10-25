// Money Decoded timeline UI: big yellow time stamps, kinetic key words, a timeline bar along the bottom.
import React from 'react';
import {spring, interpolate} from 'remotion';

// brand colours (logo: navy + mint)
export const TL = {bg: '#0A1626', bg2: '#10213A', line: '#2EE6A6', glow: '#2EE6A6', warm: '#FF5A4E', gold: '#FFD23F', ink: '#EAF4FF', mute: '#5E7391',
  node: '#173052'};
const cl = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};
const sp = (f: number, at: number, d = 12, s = 180) => spring({frame: f - at, fps: 30, config: {damping: d, stiffness: s}});

// ---------- typography & UI ----------
export const BigStamp: React.FC<{text: string; at: number; f: number; x: number; y: number; color?: string; size?: number}> = ({text, at, f, x, y, color = TL.gold, size = 150}) => {
  const p = sp(f, at, 11, 220);
  if (f < at) return null;
  return <text x={x} y={y} fontFamily="F_anton" fontSize={size} fill={color} opacity={Math.min(1, p * 1.5)}
    transform={`translate(${x} ${y}) scale(${0.6 + 0.4 * p}) translate(${-x} ${-y})`} letterSpacing={2}>{text}</text>;
};

export const Words: React.FC<{words: string[]; at: number; f: number; x: number; y: number; size?: number; accent?: number; maxW?: number}> = ({words, at, f, x, y, size = 78, accent = -1, maxW = 820}) => {
  // greedy wrap by estimate, real spacing by the browser (one <text> per line, a <tspan> per word)
  const lines: number[][] = [[]]; let w = 0;
  words.forEach((wd, i) => { const ww = wd.length * size * 0.5; if (w > 0 && w + ww > maxW) { lines.push([]); w = 0; } lines[lines.length - 1].push(i); w += ww + size * 0.3; });
  const acc = accent < 0 ? words.length + accent : accent;
  return <g>{lines.map((ln, li) => {
    const t0 = at + ln[0] * 5; const p = sp(f, t0, 12, 200);
    return <text key={li} x={x} y={y + li * size * 1.1 + (1 - Math.min(1, p)) * 30} fontFamily="F_anton" fontSize={size} xmlSpace="preserve">
      {ln.map((i) => { const q = sp(f, at + i * 5, 12, 200);
        return <tspan key={i} fill={i === acc ? TL.line : TL.ink} fillOpacity={f < at + i * 5 ? 0 : Math.min(1, q * 1.6)}>{words[i] + (i === ln[ln.length - 1] ? '' : '  ')}</tspan>; })}
    </text>;
  })}</g>;
};

export const Counter: React.FC<{from: number; to: number; at: number; f: number; x: number; y: number; unit: string; label: string; color?: string; dur?: number}> =
  ({from, to, at, f, x, y, unit, label, color = TL.line, dur = 60}) => {
  if (f < at) return null;
  const v = Math.round(interpolate(f, [at, at + dur], [from, to], {...cl, easing: (t) => 1 - Math.pow(1 - t, 3)}));
  const o = interpolate(f, [at, at + 8], [0, 1], cl);
  return <g opacity={o}>
    <text x={x} y={y} fontFamily="F_anton" fontSize={130} fill={color}>{v}<tspan fontSize={60} dx={10}>{unit}</tspan></text>
    <text x={x} y={y + 54} fontFamily="F_inter" fontWeight={700} fontSize={30} letterSpacing={4} fill={TL.mute}>{label}</text>
  </g>;
};

// timeline bar along the bottom: milestones light up as the story moves
export const TimeBar: React.FC<{marks: string[]; active: number; f: number; at: number}> = ({marks, active, f, at}) => {
  const x0 = 140, x1 = 1780, y = 1000;
  const step = (x1 - x0) / (marks.length - 1);
  const pos = interpolate(f, [at, at + 20], [Math.max(0, active - 1), active], cl);
  return <g>
    <line x1={x0} y1={y} x2={x1} y2={y} stroke={TL.mute} strokeWidth={6} strokeLinecap="round" />
    <line x1={x0} y1={y} x2={x0 + step * pos} y2={y} stroke={TL.line} strokeWidth={6} strokeLinecap="round" />
    {marks.map((m, i) => <g key={i}>
      <circle cx={x0 + step * i} cy={y} r={i <= active ? 14 : 10} fill={i <= active ? TL.line : TL.bg} stroke={i <= active ? TL.line : TL.mute} strokeWidth={4} />
      <text x={x0 + step * i} y={y - 30} textAnchor="middle" fontFamily="F_anton" fontSize={30} fill={i === active ? TL.ink : TL.mute}>{m}</text>
    </g>)}
    <circle cx={x0 + step * pos} cy={y} r={22 + 4 * Math.sin(f / 5)} fill="none" stroke={TL.line} strokeWidth={4} opacity={0.6} />
  </g>;
};


// Fallback thumbnail of Money Decoded: one big clear subject image + a huge number + 2-3 words, in the channel colours.
import React from 'react';
import {AbsoluteFill, Img, staticFile} from 'remotion';
import './theme';

const fitText = (words: string[], w: number, h: number, max = 170, min = 56) => {
  for (let s = max; s >= min; s -= 6) {
    let lines = 1, cur = 0, ok = true;
    for (const wd of words) {
      const ww = wd.length * s * 0.5;
      if (ww > w) { ok = false; break; }
      if (cur === 0) cur = ww; else if (cur + s * 0.28 + ww <= w) cur += s * 0.28 + ww; else { lines++; cur = ww; }
    }
    if (ok && lines * s * 1.08 <= h) return s;
  }
  return min;
};

const NUM = ['#FFD23F', '#FF5A4E', '#2EE6A6'];
export const ThumbTL: React.FC<{number: string; words: string; subject?: string; ar?: number; v?: number}> = ({number, words, subject, ar = 1, v = 0}) => {
  const col = NUM[(v || 0) % 3];
  const ws = (words || '').toUpperCase().split(/\s+/).filter(Boolean);
  const wSize = fitText(ws, 860, 330, 190, 90);
  const nSize = Math.min(330, Math.floor(860 / Math.max(2, (number || '').length * 0.5)));
  let h = 980, w = h * ar; if (w > 1000) { w = 1000; h = w / ar; }
  return <AbsoluteFill style={{background: 'radial-gradient(circle at 72% 50%, #14406B 0%, #0A1626 62%)'}}>
    <div style={{position: 'absolute', left: 1400 - 430, top: 540 - 430, width: 860, height: 860, borderRadius: 430,
      background: `radial-gradient(circle, ${col}55 0%, transparent 65%)`}} />
    {subject && <Img src={staticFile(subject)} style={{position: 'absolute', left: 1420 - w / 2, top: 540 - h / 2, width: w, height: h, objectFit: 'contain',
      filter: 'drop-shadow(0 20px 40px rgba(0,0,0,0.6))'}} />}
    <div style={{position: 'absolute', left: 70, top: 70, width: 900, fontFamily: 'F_anton', fontSize: nSize, lineHeight: 1, color: col,
      textShadow: '0 8px 0 rgba(0,0,0,0.55), 0 0 40px rgba(0,0,0,0.6)', whiteSpace: 'nowrap'}}>{number}</div>
    <div style={{position: 'absolute', left: 70, top: 120 + nSize, width: 880, height: 330, display: 'flex', flexWrap: 'wrap', alignContent: 'flex-start',
      gap: `0 ${wSize * 0.25}px`, fontFamily: 'F_anton', fontSize: wSize, lineHeight: 1.04}}>
      {ws.map((x, i) => <span key={i} style={{color: i === ws.length - 1 ? '#2EE6A6' : '#FFFFFF', textShadow: '0 6px 0 rgba(0,0,0,0.6)'}}>{x}</span>)}
    </div>
    <div style={{position: 'absolute', inset: 0, border: '14px solid #2EE6A6', opacity: 0.85}} />
  </AbsoluteFill>;
};

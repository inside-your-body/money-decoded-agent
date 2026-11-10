// Persian thumbnail (owner Nov 8: the channel is now Persian). The image model cannot spell Persian, so the picture is generated
// WITHOUT text (dark top band left empty) and the headline is set here in Vazirmatn Black: white, the key word in yellow,
// thick dark outline, right-to-left, auto-fitted to the top of the frame.
import React from 'react';
import {AbsoluteFill, Img, staticFile} from 'remotion';
import './theme';

const fit = (words: string[], w: number, h: number, max = 230, min = 90) => {
  for (let s = max; s >= min; s -= 6) {
    let lines = 1, cur = 0, ok = true;
    for (const wd of words) {
      const ww = wd.length * s * 0.56;
      if (ww > w) { ok = false; break; }
      if (cur === 0) cur = ww; else if (cur + s * 0.3 + ww <= w) cur += s * 0.3 + ww; else { lines++; cur = ww; }
    }
    if (ok && lines <= 2 && lines * s * 1.25 <= h) return s;
  }
  return min;
};

export const ThumbFa: React.FC<{bg: string; text: string; key_word?: string}> = ({bg, text, key_word}) => {
  const ws = (text || '').split(/\s+/).filter(Boolean).slice(0, 6);
  const size = fit(ws, 1780, 470);
  const hi = key_word ? ws.findIndex((w) => key_word.includes(w) || w.includes(key_word)) : ws.length - 1;
  return <AbsoluteFill style={{background: '#0A1626'}}>
    {bg && <Img src={staticFile(bg)} style={{position: 'absolute', inset: 0, width: 1920, height: 1080, objectFit: 'cover'}} />}
    <div style={{position: 'absolute', left: 0, top: 0, width: 1920, height: 560,
      background: 'linear-gradient(180deg, rgba(6,14,28,0.85) 0%, rgba(6,14,28,0.55) 60%, rgba(6,14,28,0) 100%)'}} />
    <div style={{position: 'absolute', left: 70, right: 70, top: 40, height: 500, display: 'flex', flexWrap: 'wrap', alignContent: 'center',
      justifyContent: 'center', gap: `0 ${size * 0.28}px`, direction: 'rtl', fontFamily: 'F_lalezar', fontSize: size, lineHeight: 1.3}}>
      {ws.map((x, i) => <span key={i} style={{color: i === (hi < 0 ? ws.length - 1 : hi) ? '#FFD23F' : '#FFFFFF',
        WebkitTextStroke: `${Math.round(size * 0.07)}px #08101E`, paintOrder: 'stroke fill',
        textShadow: `0 ${Math.round(size * 0.06)}px 0 rgba(0,0,0,0.75), 0 0 ${Math.round(size * 0.25)}px rgba(0,0,0,0.6)`}}>{x.replace(/[0-9]/g, (d) => '۰۱۲۳۴۵۶۷۸۹'[+d]).replace(/%/g, '٪')}</span>)}
    </div>
  </AbsoluteFill>;
};

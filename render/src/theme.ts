import {staticFile, delayRender, continueRender} from 'remotion';

export type Theme = {
  id: string; bg: string; bg2: string; fg: string; muted: string; accent: string; accent2: string; accent3: string;
  fontHead: string; fontBody: string; upper: boolean; pattern: string; transition: string;
  spring: [number, number]; radius: number;
};

export type Beat = {
  from: number; to: number; kind: string; text?: string; value?: string | null;
  items?: string[] | null; img?: string | null; part?: string; motion?: string | null; cast?: string[] | null; params?: any; words?: [string, number][];
};
export type Word = {w: string; s: number; e: number};
export type Props = {
  kind: 'long' | 'short'; fps: number; frames: number; theme: Theme; beats: Beat[]; words: Word[];
  channel: string; title: string;
};

const FONTS = ['anton', 'inter', 'spacemono', 'bebas', 'montserrat', 'playfair', 'poppins', 'archivoblack', 'dmserif', 'fredoka'];
if (typeof document !== 'undefined') {
  const h = delayRender('fonts');
  Promise.all(FONTS.map((f) => new FontFace('F_' + f, `url(${staticFile('fonts/' + f + '.woff2')})`, {weight: '100 900'})
    .load().then((x) => (document as any).fonts.add(x)).catch(() => null)))
    .then(() => continueRender(h));
}
export const ff = (name: string) => `F_${name}, Inter, Arial, sans-serif`;

// hex -> rgba helper
export const alpha = (hex: string, a: number) => {
  const h = hex.replace('#', '');
  const n = parseInt(h.length === 3 ? h.split('').map((c) => c + c).join('') : h, 16);
  return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${a})`;
};

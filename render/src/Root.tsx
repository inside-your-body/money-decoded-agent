import React from 'react';
import {Composition} from 'remotion';
import {TLEpisode, tlMeta} from './TLEpisode';
import {ThumbTL} from './ThumbTL';
import './theme';

export const Root: React.FC = () => (
  <>
    <Composition id="TLLong" component={TLEpisode as any} width={1920} height={1080} fps={30} durationInFrames={300} calculateMetadata={tlMeta as any} defaultProps={{beats: [], marks: [], frames: 300}} />
    <Composition id="TLShort" component={TLEpisode as any} width={1080} height={1920} fps={30} durationInFrames={300} calculateMetadata={tlMeta as any} defaultProps={{beats: [], marks: [], frames: 300, vertical: true}} />
    <Composition id="ThumbTL" component={ThumbTL as any} width={1920} height={1080} fps={30} durationInFrames={1} defaultProps={{number: "$65B", words: "PONZI SCHEME", v: 0}} />
  </>
);

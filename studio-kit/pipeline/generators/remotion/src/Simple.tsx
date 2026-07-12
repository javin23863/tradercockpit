import React from 'react';
import { AbsoluteFill } from 'remotion';

export const SimpleReel: React.FC = () => {
  return (
    <AbsoluteFill style={{ background: '#000' }}>
      <div style={{ color: '#fff' }}>Simple Test</div>
    </AbsoluteFill>
  );
};

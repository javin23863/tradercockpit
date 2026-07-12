import { registerRoot } from 'remotion';
import { SimpleReel } from './Simple';

const Comp: React.FC = () => (
  <>
    <div id="SimpleReel" data-component={SimpleReel} data-duration-in-frames={30} data-fps={30} data-width={1080} data-height={1920} />
  </>
);

registerRoot(() => Comp);

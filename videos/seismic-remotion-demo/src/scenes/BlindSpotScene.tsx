import {interpolate, useCurrentFrame} from "remotion";
import {COLORS} from "../constants";
import {Edge, Frame, Headline, Kicker, Node, ease} from "../components";

export const BlindSpotScene: React.FC<{duration: number}> = ({duration}) => {
  const frame = useCurrentFrame();
  const split = ease(frame, 76, 36);
  return <Frame duration={duration} index={1} label="THE BLIND SPOT">
    <div style={{position: "absolute", left: 108, top: 218, opacity: ease(frame, 10), translate: `0 ${interpolate(ease(frame, 10), [0,1], [24,0])}px`}}>
      <Kicker>Similarity is not dependency proof</Kicker>
      <Headline style={{marginTop: 30}}>The edit looks local.<br/><span style={{color: COLORS.orange}}>The break is not.</span></Headline>
      <div style={{marginTop: 36, maxWidth: 680, color: COLORS.muted, fontSize: 28, lineHeight: 1.4}}>Agents need the caller, test and entry point behind every impact claim.</div>
    </div>
    <div style={{position: "absolute", right: 90, top: 236, width: 640, height: 600, opacity: split}}>
      <Node x={0} y={210} label="calculate" kind="CHANGE" active delay={80}/>
      <Node x={390} y={40} label="test_checkout" kind="TEST" delay={110}/>
      <Node x={390} y={210} label="total" kind="FUNCTION" active delay={122}/>
      <Node x={390} y={380} label="handler" kind="ENTRYPOINT" delay={134}/>
      <Edge x1={214} y1={254} x2={390} y2={84} label="TESTS" delay={108}/>
      <Edge x1={214} y1={254} x2={390} y2={254} label="CALLS" active delay={120}/>
      <Edge x1={214} y1={254} x2={390} y2={424} label="CALLS" delay={132}/>
    </div>
  </Frame>;
};

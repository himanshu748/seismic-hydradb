import {interpolate, useCurrentFrame} from "remotion";
import {COLORS} from "../constants";
import {Frame, Headline, Kicker, Terminal, ease} from "../components";

export const AbstentionScene: React.FC<{duration: number}> = ({duration}) => {
  const frame = useCurrentFrame();
  return <Frame duration={duration} index={4} label="NO PATH, NO CLAIM">
    <div style={{position: "absolute", left: 106, top: 220, width: 760}}>
      <Kicker tone={COLORS.verified}>Conservative by design</Kicker>
      <Headline size={88} style={{marginTop: 30}}>When the graph cannot prove it,<br/><span style={{color: COLORS.verified}}>Seismic abstains.</span></Headline>
      <div style={{marginTop: 38, fontSize: 27, color: COLORS.muted, lineHeight: 1.45}}>No invented dependency. No similarity-shaped guess. No unsupported confidence.</div>
    </div>
    <Terminal revealAt={50} style={{position: "absolute", right: 100, top: 250, width: 760, height: 500, opacity: ease(frame, 30), translate: `${interpolate(ease(frame,30),[0,1],[50,0])}px 0`}} lines={[
      {text: "> analyze_change(targets=[\"server.py::not_real\"])", tone: COLORS.muted},
      {text: "resolved_targets: []"},
      {text: "results: []"},
      {text: "abstained: true", tone: COLORS.verified},
      {text: "reason: target not present in active snapshot", tone: COLORS.verified},
    ]}/>
  </Frame>;
};

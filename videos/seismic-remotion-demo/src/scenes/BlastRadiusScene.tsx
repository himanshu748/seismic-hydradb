import {interpolate, useCurrentFrame} from "remotion";
import {COLORS} from "../constants";
import {Edge, Frame, Kicker, Node, Panel, ease} from "../components";

const impacts = [
  ["total", "risk 0.84", "1 hop"],
  ["handler", "risk 0.72", "2 hops"],
  ["test_total", "risk 0.67", "2 hops"],
  ["checkout", "risk 0.61", "3 hops"],
  ["pricing_cli", "risk 0.58", "3 hops"],
];

export const BlastRadiusScene: React.FC<{duration: number}> = ({duration}) => {
  const frame = useCurrentFrame();
  const pulse = interpolate(frame % 96, [0, 48, 96], [0.3, 1, 0.3]);
  return <Frame duration={duration} index={3} label="EXACT BLAST RADIUS">
    <div style={{position: "absolute", left: 92, right: 92, top: 150, bottom: 110, display: "grid", gridTemplateColumns: "1fr 420px", gap: 22}}>
      <Panel style={{position: "relative", overflow: "hidden", opacity: ease(frame, 12)}}>
        <div style={{position: "absolute", left: 34, top: 28}}><Kicker>Changed target</Kicker><div style={{fontFamily: "Seismic Mono", fontSize: 21, marginTop: 14}}>pricing.py::calculate</div></div>
        <Node x={70} y={318} label="calculate" kind="CHANGE" active delay={40}/>
        <Node x={440} y={318} label="total" kind="FUNCTION" active delay={72}/>
        <Node x={810} y={318} label="handler" kind="ENTRYPOINT" active delay={104}/>
        <Node x={440} y={105} label="test_total" kind="TEST" delay={118}/>
        <Node x={810} y={545} label="pricing_cli" kind="ENTRYPOINT" delay={132}/>
        <Edge x1={284} y1={362} x2={440} y2={362} label="CALLS" active delay={68}/>
        <Edge x1={654} y1={362} x2={810} y2={362} label="CALLS" active delay={100}/>
        <Edge x1={547} y1={318} x2={547} y2={193} label="TESTS" delay={114}/>
        <Edge x1={917} y1={406} x2={917} y2={545} label="STARTS_AT" delay={128}/>
        <div style={{position: "absolute", left: 284, top: 357, width: 526, height: 10, background: `rgba(255,90,36,${0.12*pulse})`, filter: "blur(7px)"}} />
        <div style={{position: "absolute", left: 70, bottom: 34, padding: "13px 16px", background: "rgba(255,90,36,.08)", borderLeft: `3px solid ${COLORS.orange}`, fontFamily: "Seismic Mono", fontSize: 16, color: COLORS.muted}}>calculate → total → handler · 2 hops · CALLS × 2</div>
      </Panel>
      <Panel style={{padding: "30px 28px", opacity: ease(frame, 52)}}>
        <div style={{display: "flex", justifyContent: "space-between", alignItems: "center"}}><Kicker>Ranked impacts</Kicker><span style={{fontFamily: "Seismic Mono", color: COLORS.verified}}>5 FOUND</span></div>
        <div style={{marginTop: 24}}>{impacts.map((impact,index)=><div key={impact[0]} style={{padding: "19px 0", borderTop: `1px solid ${COLORS.border}`, opacity: ease(frame, 76+index*15), background: index===1 ? "rgba(255,90,36,.06)" : "transparent"}}><div style={{display: "flex", justifyContent: "space-between", fontFamily: "Seismic Mono", fontSize: 18}}><strong style={{color: index===1 ? COLORS.orange : COLORS.paper}}>{impact[0]}</strong><span>{impact[1]}</span></div><div style={{marginTop: 8, color: COLORS.muted, fontSize: 15}}>{impact[2]} · exact evidence path</div></div>)}</div>
      </Panel>
    </div>
  </Frame>;
};

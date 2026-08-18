import {interpolate, useCurrentFrame} from "remotion";
import {COLORS} from "../constants";
import {Edge, Frame, Headline, Kicker, Node, Panel, ease} from "../components";

const procedures = [
  ["algo.SSpaths", "one changed target"],
  ["algo.MSpaths", "multiple changed targets"],
  ["algo.SPpaths", "one exact impact proof"],
];

export const NativeGraphScene: React.FC<{duration: number}> = ({duration}) => {
  const frame = useCurrentFrame();
  return <Frame duration={duration} index={6} label="HYDRADB NATIVE">
    <div style={{position: "absolute", left: 102, top: 180, width: 710}}>
      <Kicker>System of record + path engine</Kicker>
      <Headline size={80} style={{marginTop: 30}}>Paths are the<br/><span style={{color: COLORS.orange}}>product primitive.</span></Headline>
      <div style={{marginTop: 42, display: "grid", gap: 13}}>{procedures.map((item,index)=><Panel key={item[0]} style={{padding: "20px 22px", display: "grid", gridTemplateColumns: "220px 1fr", alignItems: "center", opacity: ease(frame,48+index*22)}}><strong style={{fontFamily: "Seismic Mono", color: COLORS.orange, fontSize: 18}}>{item[0]}</strong><span style={{color: COLORS.muted, fontSize: 18}}>{item[1]}</span></Panel>)}</div>
      <div style={{marginTop: 32, color: COLORS.muted, fontSize: 22, lineHeight: 1.4, opacity: ease(frame,130)}}>Not a log sink. Remove HydraDB and the gate loses direction, reachability and proof.</div>
    </div>
    <Panel style={{position: "absolute", right: 92, top: 175, width: 900, height: 700, opacity: ease(frame,24), translate: `${interpolate(ease(frame,24),[0,1],[44,0])}px 0`}}>
      <div style={{position: "absolute", top: 28, left: 34, fontFamily: "Seismic Mono", color: COLORS.verified, fontSize: 15}}>INCIDENT EVIDENCE ACROSS SNAPSHOTS</div>
      <Node x={55} y={145} label="calculate@a91" kind="SNAPSHOT A" active delay={55}/>
      <Node x={345} y={145} label="pricing-identity" kind="STABLE IDENTITY" delay={82}/>
      <Node x={635} y={145} label="calculate@b42" kind="SNAPSHOT B" active delay={110}/>
      <Edge x1={269} y1={189} x2={345} y2={189} label="INSTANCE_OF" delay={76}/>
      <Edge x1={559} y1={189} x2={635} y2={189} label="INSTANCE_OF" delay={104}/>
      <Node x={345} y={390} label="checkout failure" kind="INCIDENT" delay={138}/>
      <Edge x1={452} y1={233} x2={452} y2={390} label="TRIGGERED_BY" active delay={132}/>
      <div style={{position: "absolute", left: 54, right: 54, bottom: 42, padding: "18px 20px", borderLeft: `3px solid ${COLORS.verified}`, background: "rgba(143,163,123,.07)", color: COLORS.muted, fontSize: 19, lineHeight: 1.45, opacity: ease(frame,165)}}>Old commits stay immutable. New rankings can still learn from exact historical breakage.</div>
    </Panel>
  </Frame>;
};

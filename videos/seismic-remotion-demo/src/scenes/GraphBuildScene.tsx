import {interpolate, useCurrentFrame} from "remotion";
import {COLORS} from "../constants";
import {Edge, Frame, Headline, Kicker, Node, Panel, ease} from "../components";

export const GraphBuildScene: React.FC<{duration: number}> = ({duration}) => {
  const frame = useCurrentFrame();
  return <Frame duration={duration} index={2} label="BUILD THE GRAPH">
    <div style={{position: "absolute", left: 100, top: 180, width: 650}}>
      <Kicker>One Git commit, one immutable snapshot</Kicker>
      <Headline size={82} style={{marginTop: 30}}>Code becomes<br/><span style={{color: COLORS.orange}}>queryable structure.</span></Headline>
      <div style={{display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, marginTop: 44}}>
        {["FILE", "FUNCTION", "TEST", "ENTRYPOINT"].map((kind, index) => <Panel key={kind} style={{padding: "22px 24px", opacity: ease(frame, 72 + index * 15)}}><div style={{fontFamily: "Seismic Mono", color: COLORS.orange, fontSize: 16}}>{kind}</div><div style={{color: COLORS.muted, marginTop: 9, fontSize: 17}}>Artifact node</div></Panel>)}
      </div>
    </div>
    <Panel style={{position: "absolute", right: 90, top: 170, width: 910, height: 720, opacity: ease(frame, 35), translate: `${interpolate(ease(frame,35),[0,1],[50,0])}px 0`}}>
      <div style={{position: "absolute", left: 36, top: 26, fontFamily: "Seismic Mono", fontSize: 15, color: COLORS.verified}}>HYDRADB / ACTIVE SNAPSHOT 9015879B1A</div>
      <Node x={48} y={135} label="server.py" kind="FILE" delay={52}/>
      <Node x={348} y={70} label="_bounded_int" kind="FUNCTION" active delay={72}/>
      <Node x={348} y={260} label="http_main" kind="FUNCTION" delay={92}/>
      <Node x={648} y={110} label="seismic-http" kind="ENTRYPOINT" delay={112}/>
      <Node x={648} y={355} label="transport test" kind="TEST" delay={132}/>
      <Edge x1={262} y1={179} x2={348} y2={114} label="PART_OF" delay={66}/>
      <Edge x1={455} y1={158} x2={455} y2={260} label="CALLS" active delay={88}/>
      <Edge x1={562} y1={304} x2={648} y2={154} label="STARTS_AT" delay={106}/>
      <Edge x1={562} y1={304} x2={648} y2={399} label="TESTS" delay={126}/>
      <div style={{position: "absolute", left: 48, right: 48, bottom: 42, display: "flex", gap: 10, flexWrap: "wrap"}}>
        {["CALLS", "IMPORTS", "TESTS", "STARTS_AT", "DEPENDS_ON"].map((edge, index) => <span key={edge} style={{padding: "9px 13px", border: `1px solid ${COLORS.border}`, borderRadius: 7, fontFamily: "Seismic Mono", fontSize: 13, color: index===0 ? COLORS.orange : COLORS.muted, opacity: ease(frame,150+index*8)}}>{edge}</span>)}
      </div>
    </Panel>
  </Frame>;
};

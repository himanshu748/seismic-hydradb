import {interpolate, useCurrentFrame} from "remotion";
import {COLORS} from "../constants";
import {Edge, Frame, Kicker, Node, Panel, ease} from "../components";

const impacts = [
  ["http_main", "68.00", "1 hop"],
  ["seismic-http", "40.00", "2 hops"],
  ["transport test", "36.00", "2 hops"],
];

export const BlastRadiusScene: React.FC<{duration: number}> = ({duration}) => {
  const frame = useCurrentFrame();
  const pulse = interpolate(frame % 96, [0, 48, 96], [0.3, 1, 0.3]);
  return <Frame duration={duration} index={3} label="EXACT BLAST RADIUS">
    <div style={{position: "absolute", left: 92, right: 92, top: 150, bottom: 110, display: "grid", gridTemplateColumns: "1fr 430px", gap: 22}}>
      <Panel style={{position: "relative", overflow: "hidden", opacity: ease(frame, 0, 8)}}>
        <div style={{position: "absolute", left: 34, top: 28}}>
          <Kicker>Real self-analysis</Kicker>
          <div style={{fontFamily: "Seismic Mono", fontSize: 19, marginTop: 14}}>src/seismic/server.py::_bounded_int</div>
        </div>
        <Node x={64} y={318} label="_bounded_int" kind="CHANGE" active delay={52}/>
        <Node x={410} y={318} label="http_main" kind="CALLER" active delay={104}/>
        <Node x={770} y={166} label="seismic-http" kind="ENTRYPOINT" active delay={176}/>
        <Node x={770} y={482} label="transport test" kind="TEST" delay={220}/>
        <Edge x1={278} y1={362} x2={410} y2={362} label="CALLS" active delay={92}/>
        <Edge x1={624} y1={362} x2={770} y2={210} label="STARTS_AT" active delay={160}/>
        <Edge x1={624} y1={362} x2={770} y2={526} label="TESTS" delay={204}/>
        <div style={{position: "absolute", left: 278, top: 357, width: 492, height: 10, background: `rgba(255,90,36,${0.12*pulse})`, filter: "blur(7px)"}} />
        <div style={{position: "absolute", left: 64, bottom: 34, padding: "13px 16px", background: "rgba(255,90,36,.08)", borderLeft: `3px solid ${COLORS.orange}`, fontFamily: "Seismic Mono", fontSize: 16, color: COLORS.muted, opacity: ease(frame, 255)}}>_bounded_int → http_main → seismic-http · 2 hops</div>
      </Panel>
      <Panel style={{padding: "28px 26px", opacity: ease(frame, 245), translate: `${interpolate(ease(frame,245),[0,1],[36,0])}px 0`}}>
        <div style={{display: "flex", justifyContent: "space-between", alignItems: "center"}}><Kicker>Agent gate</Kicker><span style={{fontFamily: "Seismic Mono", color: COLORS.warning}}>REVIEW</span></div>
        <div style={{marginTop: 20, padding: "18px", borderLeft: `3px solid ${COLORS.warning}`, background: "rgba(243,173,50,.06)"}}>
          <div style={{fontFamily: "Seismic Display", fontSize: 27, fontWeight: 700}}>Review graph evidence</div>
          <div style={{marginTop: 10, color: COLORS.muted, lineHeight: 1.4}}>3 supported impacts · 68.00 max risk</div>
        </div>
        <div style={{marginTop: 18}}>{impacts.map((impact,index)=><div key={impact[0]} style={{padding: "14px 0", borderTop: `1px solid ${COLORS.border}`, opacity: ease(frame, 300+index*28)}}><div style={{display: "flex", justifyContent: "space-between", fontFamily: "Seismic Mono", fontSize: 17}}><strong style={{color: index===0 ? COLORS.orange : COLORS.paper}}>{impact[0]}</strong><span>{impact[1]}</span></div><div style={{marginTop: 6, color: COLORS.muted, fontSize: 14}}>{impact[2]} · exact path</div></div>)}</div>
        <div style={{marginTop: 18, fontFamily: "Seismic Mono", fontSize: 13, lineHeight: 1.5, color: COLORS.verified, opacity: ease(frame, 405)}}>RUN BEFORE MERGE<br/>pytest tests/test_server.py::<br/>test_http_entrypoint_forces_stateless_json_transport</div>
      </Panel>
    </div>
  </Frame>;
};

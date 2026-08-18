import {interpolate, useCurrentFrame} from "remotion";
import {COLORS} from "../constants";
import {CountUp, Frame, Kicker, Reveal, Sheet, Status, ease} from "../components";

const route = [
  {label: "_bounded_int", x: 72, y: 278},
  {label: "http_main", x: 392, y: 278},
  {label: "seismic-http", x: 712, y: 126},
  {label: "transport test", x: 712, y: 430},
];

export const BlastRadiusScene: React.FC<{duration: number}> = ({duration}) => {
  const frame = useCurrentFrame();
  const trace = interpolate(frame, [90, 265], [0, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
  return <Frame duration={duration} index={3} label="THE AGENT DECISION ROOM" mode="orange">
    <div style={{position: "absolute", inset: 0, paddingTop: 24}}>
      <Reveal at={4}>
        <div style={{display: "flex", alignItems: "center", justifyContent: "space-between"}}>
          <div><Kicker dark>Real self-analysis · Seismic changes Seismic</Kicker><div style={{fontFamily: "Seismic Display", fontSize: 67, fontWeight: 700, letterSpacing: "-.055em", marginTop: 18}}>A diff enters. A decision leaves.</div></div>
          <Status tone="ink">HYDRADB PATH PROOF</Status>
        </div>
      </Reveal>
      <div style={{display: "grid", gridTemplateColumns: "355px 1fr 390px", gap: 20, height: 654, marginTop: 30}}>
        <Reveal at={34} from="left" style={{height: "100%"}}>
          <Sheet mode="paper" style={{height: "100%", padding: "25px 23px", background: COLORS.paper}}>
            <div style={{fontFamily: "Seismic Mono", fontSize: 13, color: "#746b63"}}>CHANGE PACKET 01</div>
            <div style={{fontFamily: "Seismic Display", fontSize: 31, fontWeight: 700, marginTop: 26}}>server.py</div>
            <div style={{fontFamily: "Seismic Mono", fontSize: 15, marginTop: 8, color: COLORS.orange}}>::_bounded_int</div>
            <div style={{marginTop: 36, borderTop: "1px solid rgba(18,16,14,.15)", borderBottom: "1px solid rgba(18,16,14,.15)", padding: "22px 0", fontFamily: "Seismic Mono", fontSize: 14, lineHeight: 1.8}}>
              <div style={{color: "#81766d"}}>- os.getenv(name)</div>
              <div style={{color: COLORS.orange}}>+ os.getenv(name, "")</div>
              <div style={{color: COLORS.orange}}>&nbsp;&nbsp;.strip() or None</div>
            </div>
            <div style={{display: "grid", gap: 14, marginTop: 32}}>{["resolve changed lines", "walk reverse edges", "rank exact impacts"].map((step, index) => <div key={step} style={{display: "flex", gap: 12, alignItems: "center", fontSize: 15, opacity: ease(frame, 90 + index * 42)}}><span style={{width: 25, height: 25, borderRadius: 99, background: COLORS.graphite, color: COLORS.paper, display: "grid", placeItems: "center", fontFamily: "Seismic Mono", fontSize: 11}}>{index + 1}</span>{step}</div>)}</div>
          </Sheet>
        </Reveal>
        <Reveal at={58} from="scale" style={{height: "100%"}}>
          <Sheet style={{height: "100%", position: "relative", background: COLORS.graphite, color: COLORS.paper, overflow: "hidden"}}>
            <div style={{position: "absolute", left: 25, top: 22, fontFamily: "Seismic Mono", fontSize: 12, letterSpacing: ".14em", color: COLORS.muted}}>NATIVE REVERSE DEPENDENCY WALK</div>
            <svg viewBox="0 0 990 654" style={{position: "absolute", inset: 0, width: "100%", height: "100%"}}>
              <path d="M178 342 L498 342 L818 190" fill="none" stroke={COLORS.border} strokeWidth="3" />
              <path d="M498 342 L818 494" fill="none" stroke={COLORS.border} strokeWidth="3" />
              <path d="M178 342 L498 342 L818 190" fill="none" stroke={COLORS.orange} strokeWidth="5" pathLength="1" strokeDasharray="1" strokeDashoffset={1-trace} />
              <path d="M498 342 L818 494" fill="none" stroke={COLORS.verified} strokeWidth="4" pathLength="1" strokeDasharray="1" strokeDashoffset={1-Math.max(0, trace-.35)} />
            </svg>
            {route.map((node, index) => <div key={node.label} style={{position: "absolute", left: node.x, top: node.y, width: 220, padding: "18px", borderRadius: 12, border: `2px solid ${index === 3 ? COLORS.verified : COLORS.orange}`, background: index === 0 ? COLORS.orange : "#1d1916", color: index === 0 ? COLORS.graphite : COLORS.paper, fontFamily: "Seismic Mono", fontSize: 17, fontWeight: 700, opacity: ease(frame, 90 + index * 44), transform: `scale(${interpolate(ease(frame, 90 + index * 44), [0, 1], [.75, 1])})`}}>{node.label}<div style={{fontSize: 11, marginTop: 8, fontWeight: 400, opacity: .7}}>{index === 0 ? "CHANGE" : index === 1 ? "CALLER" : index === 2 ? "ENTRYPOINT" : "REQUIRED TEST"}</div></div>)}
            <div style={{position: "absolute", left: 26, bottom: 22, fontFamily: "Seismic Mono", fontSize: 14, color: COLORS.verified, opacity: ease(frame, 285)}}>EXACT PATH · 2 HOPS · NO VECTOR GUESS</div>
          </Sheet>
        </Reveal>
        <Reveal at={265} from="right" style={{height: "100%"}}>
          <Sheet mode="paper" style={{height: "100%", padding: "26px", background: COLORS.paper, display: "flex", flexDirection: "column"}}>
            <div style={{display: "flex", justifyContent: "space-between", alignItems: "center"}}><span style={{fontFamily: "Seismic Mono", fontSize: 13, color: "#746b63"}}>AGENT GATE</span><Status tone="yellow">REVIEW</Status></div>
            <div style={{marginTop: 28, fontFamily: "Seismic Display", fontSize: 34, fontWeight: 700}}>Review before editing</div>
            <div style={{marginTop: 12, color: "#70665e", lineHeight: 1.45}}>Three supported impacts carry inspectable HydraDB paths.</div>
            <div style={{fontFamily: "Seismic Display", fontSize: 95, fontWeight: 700, color: COLORS.orange, marginTop: 36, lineHeight: .9}}><CountUp value={3} at={300} /></div>
            <div style={{fontFamily: "Seismic Mono", fontSize: 13, color: "#70665e", marginTop: 8}}>SUPPORTED IMPACTS</div>
            <div style={{marginTop: 28, paddingTop: 22, borderTop: "1px solid rgba(18,16,14,.14)"}}>
              <div style={{fontFamily: "Seismic Mono", fontSize: 12, color: COLORS.verified}}>RUN BEFORE MERGE</div>
              <div style={{fontFamily: "Seismic Mono", fontSize: 14, lineHeight: 1.55, marginTop: 12}}>pytest tests/test_server.py::<br/>test_http_entrypoint_forces_<br/>stateless_json_transport</div>
            </div>
          </Sheet>
        </Reveal>
      </div>
    </div>
  </Frame>;
};

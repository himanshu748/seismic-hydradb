import {interpolate, useCurrentFrame} from "remotion";
import {COLORS} from "../constants";
import {CountUp, Frame, Headline, Kicker, Reveal, Sheet, Status, ease} from "../components";

const files = ["server.py", "tools.py", "gate.py", "test_server.py", "pyproject.toml"];
const artifacts = [
  {label: "_bounded_int", x: 70, y: 124, tone: COLORS.orange},
  {label: "http_main", x: 360, y: 68, tone: COLORS.graphite},
  {label: "seismic-http", x: 650, y: 156, tone: COLORS.graphite},
  {label: "transport test", x: 360, y: 300, tone: COLORS.verified},
];

export const GraphBuildScene: React.FC<{duration: number}> = ({duration}) => {
  const frame = useCurrentFrame();
  const scanY = interpolate(frame % 150, [0, 150], [0, 410]);
  return <Frame duration={duration} index={2} label="CODE BECOMES STRUCTURE" mode="paper">
    <div style={{position: "absolute", inset: 0, paddingTop: 30}}>
      <Reveal at={5}>
        <div style={{display: "flex", justifyContent: "space-between", alignItems: "flex-end"}}>
          <div><Kicker dark>Immutable repository snapshot</Kicker><Headline size={80} style={{marginTop: 20}}>From checkout to<br/><span style={{color: COLORS.orange}}>queryable evidence.</span></Headline></div>
          <Status tone="ink" style={{marginBottom: 10}}>ACTIVE SNAPSHOT · 73EF7C7</Status>
        </div>
      </Reveal>
      <div style={{display: "grid", gridTemplateColumns: "330px 110px 1fr", gap: 22, height: 570, marginTop: 42}}>
        <Reveal at={44} from="left" style={{height: "100%"}}>
          <Sheet mode="paper" style={{height: "100%", padding: "24px 22px", position: "relative", overflow: "hidden"}}>
            <div style={{fontFamily: "Seismic Mono", fontSize: 13, letterSpacing: ".13em", color: "#6f665f"}}>GIT CHECKOUT</div>
            <div style={{position: "absolute", left: 0, right: 0, top: 70 + scanY, height: 2, background: COLORS.orange, boxShadow: "0 0 18px rgba(255,90,36,.5)"}} />
            <div style={{marginTop: 26, display: "grid", gap: 13}}>{files.map((file, index) => <div key={file} style={{padding: "14px 16px", border: "1px solid rgba(18,16,14,.12)", borderRadius: 8, fontFamily: "Seismic Mono", fontSize: 15, background: index === 0 ? "rgba(255,90,36,.08)" : "rgba(255,255,255,.45)", opacity: ease(frame, 64 + index * 13)}}>{file}</div>)}</div>
          </Sheet>
        </Reveal>
        <div style={{display: "flex", alignItems: "center", justifyContent: "center"}}>
          <div style={{width: 88, height: 2, background: "#bcb1a7", position: "relative"}}><div style={{width: `${interpolate(frame, [90, 180], [0, 100], {extrapolateLeft: "clamp", extrapolateRight: "clamp"})}%`, height: "100%", background: COLORS.orange}} /><div style={{position: "absolute", right: -2, top: -6, width: 12, height: 12, borderTop: `2px solid ${COLORS.orange}`, borderRight: `2px solid ${COLORS.orange}`, rotate: "45deg"}} /></div>
        </div>
        <Reveal at={82} from="right" style={{height: "100%"}}>
          <Sheet mode="paper" style={{height: "100%", position: "relative", overflow: "hidden"}}>
            <div style={{position: "absolute", top: 22, left: 28, fontFamily: "Seismic Mono", fontSize: 13, color: COLORS.orange, letterSpacing: ".13em"}}>HYDRADB / DIRECTED CODE GRAPH</div>
            <svg style={{position: "absolute", inset: 0, width: "100%", height: "100%"}} viewBox="0 0 930 570">
              <path d="M160 215 C280 130 390 130 455 158 S670 190 755 245" fill="none" stroke="#c7bbb0" strokeWidth="2" />
              <path d="M160 215 C250 310 335 420 455 390" fill="none" stroke={COLORS.orange} strokeWidth="3" strokeDasharray="9 10" strokeDashoffset={-frame * 1.6} />
              <path d="M455 390 C570 350 650 280 755 245" fill="none" stroke="#c7bbb0" strokeWidth="2" />
            </svg>
            {artifacts.map((artifact, index) => <div key={artifact.label} style={{position: "absolute", left: artifact.x, top: artifact.y + 75, width: 210, minHeight: 86, padding: "16px", border: `2px solid ${artifact.tone}`, background: artifact.tone === COLORS.orange ? COLORS.orange : COLORS.paper, color: COLORS.graphite, borderRadius: 12, fontFamily: "Seismic Mono", fontSize: 17, fontWeight: 700, opacity: ease(frame, 130 + index * 24), transform: `scale(${interpolate(ease(frame, 130 + index * 24), [0, 1], [.7, 1])})`}}>{artifact.label}<div style={{fontSize: 11, marginTop: 9, fontWeight: 400, color: artifact.tone === COLORS.orange ? "#5b200e" : "#766c64"}}>{index === 3 ? "TEST" : index === 2 ? "ENTRYPOINT" : "FUNCTION"}</div></div>)}
            <div style={{position: "absolute", left: 28, right: 28, bottom: 24, display: "flex", justifyContent: "space-between", fontFamily: "Seismic Mono"}}>
              <span><CountUp value={276} at={230} style={{fontSize: 31, fontWeight: 700}} /> <small>ARTIFACTS</small></span>
              <span><CountUp value={535} at={245} style={{fontSize: 31, fontWeight: 700}} /> <small>RELATIONSHIPS</small></span>
              <span style={{color: COLORS.verified, opacity: ease(frame, 260)}}>IMMUTABLE ✓</span>
            </div>
          </Sheet>
        </Reveal>
      </div>
    </div>
  </Frame>;
};

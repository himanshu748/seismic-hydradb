import {interpolate, useCurrentFrame} from "remotion";
import {COLORS} from "../constants";
import {Frame, Headline, Kicker, Reveal, Sheet, Status, ease} from "../components";

const dependencyRows = [
  ["CHANGE", "_bounded_int"],
  ["CALLER", "http_main"],
  ["ENTRYPOINT", "seismic-http"],
  ["TEST", "transport test"],
];

export const BlindSpotScene: React.FC<{duration: number}> = ({duration}) => {
  const frame = useCurrentFrame();
  const beam = interpolate(frame, [85, 225], [0, 100], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
  return <Frame duration={duration} index={1} label="THE HIDDEN AFTERSHOCK" mode="dark">
    <div style={{position: "absolute", inset: 0, display: "grid", gridTemplateColumns: "1.08fr .92fr", gap: 30, paddingTop: 44}}>
      <div style={{position: "relative"}}>
        <Reveal at={8}>
          <Kicker>A one-line patch enters the agent</Kicker>
          <Headline size={105} style={{marginTop: 26, maxWidth: 900}}>One line moves.<br/><span style={{color: COLORS.orange}}>Four things feel it.</span></Headline>
        </Reveal>
        <Reveal at={64} from="left">
          <Sheet style={{marginTop: 52, width: 900, overflow: "hidden"}}>
            <div style={{padding: "18px 24px", borderBottom: `1px solid ${COLORS.border}`, display: "flex", justifyContent: "space-between", fontFamily: "Seismic Mono", fontSize: 14, color: COLORS.muted}}>
              <span>src/seismic/server.py</span><span>git diff --unified=0</span>
            </div>
            <div style={{padding: "25px 28px", fontFamily: "Seismic Mono", fontSize: 20, lineHeight: 1.85}}>
              <div style={{color: COLORS.muted}}>199&nbsp;&nbsp; raw = os.getenv(name)</div>
              <div style={{margin: "8px -28px 0", padding: "7px 28px", background: "rgba(255,90,36,.12)", color: COLORS.orange, borderLeft: `4px solid ${COLORS.orange}`}}>199+ raw = os.getenv(name, "").strip() or None</div>
            </div>
          </Sheet>
        </Reveal>
        <div style={{marginTop: 30, display: "flex", gap: 12, opacity: ease(frame, 120)}}><Status>1 CHANGED SYMBOL</Status><Status tone="yellow">UNKNOWN BLAST RADIUS</Status></div>
      </div>
      <div style={{position: "relative", padding: "76px 22px 0 48px"}}>
        <div style={{position: "absolute", left: 77, top: 130, bottom: 148, width: 2, background: COLORS.border}}>
          <div style={{width: "100%", height: `${beam}%`, background: COLORS.orange, boxShadow: "0 0 26px rgba(255,90,36,.7)"}} />
        </div>
        {dependencyRows.map((row, index) => {
          const active = ease(frame, 92 + index * 38, 16);
          return <div key={row[1]} style={{height: 132, position: "relative", display: "grid", gridTemplateColumns: "52px 1fr", alignItems: "center", opacity: active, transform: `translateX(${interpolate(active, [0, 1], [44, 0])}px)`}}>
            <span style={{width: 16, height: 16, borderRadius: 99, border: `3px solid ${COLORS.orange}`, background: index === 0 ? COLORS.orange : COLORS.graphite, zIndex: 2}} />
            <div>
              <div style={{fontFamily: "Seismic Mono", fontSize: 13, letterSpacing: ".14em", color: index === 3 ? COLORS.verified : COLORS.orange}}>{row[0]}</div>
              <div style={{fontFamily: "Seismic Display", fontSize: 36, fontWeight: 700, marginTop: 8}}>{row[1]}</div>
            </div>
          </div>;
        })}
        <div style={{fontFamily: "Seismic Mono", color: COLORS.muted, fontSize: 15, lineHeight: 1.5, opacity: ease(frame, 260)}}>Similarity sees the edit.<br/>Structure sees the aftershock.</div>
      </div>
    </div>
  </Frame>;
};

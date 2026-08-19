import {useCurrentFrame} from "remotion";
import {COLORS} from "../constants";
import {Frame, Headline, Kicker, Reveal, Sheet, Status, ease} from "../components";

const tools = [
  ["index_repository", -650, -240],
  ["analyze_change", -650, -70],
  ["analyze_diff", -650, 100],
  ["retrieve_context", 420, -240],
  ["explain_impact", 420, -70],
  ["record_incident", 420, 100],
  ["repository_status", -650, 270],
  ["decision_history", 420, 270],
] as const;

export const McpScene: React.FC<{duration: number}> = ({duration}) => {
  const frame = useCurrentFrame();
  const spin = Math.sin(frame / 52) * 8;
  return <Frame duration={duration} index={5} label="STATELESS AGENT SURFACE" mode="dark">
    <div style={{position: "absolute", inset: 0, paddingTop: 22}}>
      <Reveal at={4}>
        <div style={{display: "flex", justifyContent: "space-between", alignItems: "flex-end"}}>
          <div><Kicker>Eight agent tools around one durable core</Kicker><Headline size={76} style={{marginTop: 22}}>Fresh process.<br/><span style={{color: COLORS.orange}}>Same graph truth.</span></Headline></div>
          <div style={{display: "flex", gap: 12, marginBottom: 10}}><Status tone="green">STDIO VERIFIED</Status><Status tone="green">HTTP VERIFIED</Status></div>
        </div>
      </Reveal>
      <div style={{position: "absolute", left: "50%", top: 545, width: 0, height: 0}}>
        <div style={{position: "absolute", left: -950, top: -360, width: 1900, height: 720, border: `1px solid ${COLORS.border}`, borderRadius: "50%", opacity: .5, transform: `rotate(${spin}deg)`}} />
        <div style={{position: "absolute", left: -355, top: -230, width: 710, height: 460, borderRadius: 999, background: "radial-gradient(circle, rgba(255,90,36,.2), rgba(255,90,36,.03) 48%, transparent 70%)", border: "1px solid rgba(255,90,36,.36)", display: "grid", placeItems: "center", opacity: ease(frame, 45)}}>
          <div style={{width: 270, height: 270, borderRadius: "50%", background: COLORS.orange, color: COLORS.graphite, display: "grid", placeItems: "center", textAlign: "center", boxShadow: "0 0 80px rgba(255,90,36,.28)"}}>
            <div><div style={{fontFamily: "Seismic Display", fontSize: 44, fontWeight: 700, letterSpacing: "-.05em"}}>HydraDB</div><div style={{fontFamily: "Seismic Mono", fontSize: 12, letterSpacing: ".13em", marginTop: 12}}>DURABLE CODE GRAPH</div></div>
          </div>
        </div>
        {tools.map((tool, index) => <Reveal key={tool[0]} at={70 + index * 35} from={tool[1] < 0 ? "left" : "right"} style={{position: "absolute", left: tool[1], top: tool[2]}}>
          <Sheet style={{width: 300, padding: "18px 20px", display: "flex", alignItems: "center", gap: 13, borderColor: tool[0] === "analyze_diff" ? COLORS.orange : COLORS.border}}>
            <span style={{width: 9, height: 9, borderRadius: 99, background: tool[0] === "analyze_diff" ? COLORS.orange : COLORS.verified}} />
            <span style={{fontFamily: "Seismic Mono", fontSize: 15, color: tool[0] === "analyze_diff" ? COLORS.orange : COLORS.paper}}>{tool[0]}</span>
          </Sheet>
        </Reveal>)}
      </div>
      <div style={{position: "absolute", left: 20, bottom: 14, right: 20, display: "grid", gridTemplateColumns: "1fr auto 1fr", alignItems: "center", gap: 20, opacity: ease(frame, 410)}}>
        <div style={{height: 1, background: `linear-gradient(90deg, transparent, ${COLORS.verified})`}} />
        <div style={{fontFamily: "Seismic Mono", fontSize: 14, color: COLORS.verified}}>CLIENT STATE ENDS · GRAPH STATE SURVIVES</div>
        <div style={{height: 1, background: `linear-gradient(90deg, ${COLORS.verified}, transparent)`}} />
      </div>
      <div style={{position: "absolute", left: 720, top: 425, width: 410, height: 240, pointerEvents: "none", opacity: ease(frame, 520)}}>
        <div style={{position: "absolute", left: -490, top: 30, fontFamily: "Seismic Mono", fontSize: 13, color: COLORS.muted}}>FRESH PROCESS A</div>
        <div style={{position: "absolute", right: -490, top: 30, fontFamily: "Seismic Mono", fontSize: 13, color: COLORS.muted}}>FRESH CLIENT B</div>
      </div>
    </div>
  </Frame>;
};

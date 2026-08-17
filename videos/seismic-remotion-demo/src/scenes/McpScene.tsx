import {interpolate, useCurrentFrame} from "remotion";
import {COLORS} from "../constants";
import {Frame, Headline, Kicker, Panel, Terminal, ease} from "../components";

const tools = ["index_repository", "analyze_change", "analyze_diff", "retrieve_context", "explain_impact", "record_incident", "repository_status"];

export const McpScene: React.FC<{duration: number}> = ({duration}) => {
  const frame = useCurrentFrame();
  return <Frame duration={duration} index={5} label="STATELESS MCP">
    <div style={{position: "absolute", left: 100, top: 175, width: 690}}>
      <Kicker>Built for coding agents</Kicker>
      <Headline size={82} style={{marginTop: 30}}>Seven tools.<br/><span style={{color: COLORS.orange}}>One durable graph.</span></Headline>
      <div style={{display: "flex", flexWrap: "wrap", gap: 10, marginTop: 40}}>{tools.map((tool,index)=><span key={tool} style={{padding: "12px 14px", border: `1px solid ${index===1 ? COLORS.orange : COLORS.border}`, borderRadius: 7, color: index===1 ? COLORS.orange : COLORS.muted, background: index===1 ? "rgba(255,90,36,.07)" : COLORS.raised, fontFamily: "Seismic Mono", fontSize: 14, opacity: ease(frame,60+index*11)}}>{tool}</span>)}</div>
      <Panel style={{marginTop: 40, padding: "22px 24px", opacity: ease(frame,145)}}><div style={{fontFamily: "Seismic Mono", fontSize: 15, color: COLORS.verified}}>STATELESS HTTP = TRUE</div><div style={{marginTop: 10, color: COLORS.muted, fontSize: 18}}>Fresh client. Same HydraDB snapshot.</div></Panel>
    </div>
    <Terminal revealAt={35} style={{position: "absolute", right: 92, top: 195, width: 920, height: 650, opacity: ease(frame,22), translate: `${interpolate(ease(frame,22),[0,1],[45,0])}px 0`}} lines={[
      {text: "$ seismic  # fresh stdio MCP process", tone: COLORS.muted},
      {text: "→ tools/call analyze_change"},
      {text: "  target: pricing.py::calculate"},
      {text: "← 5 ranked impacts", tone: COLORS.orange},
      {text: "  handler  calculate → total → handler"},
      {text: "  evidence: CALLS, CALLS", tone: COLORS.verified},
      {text: "✓ durable state recovered from HydraDB", tone: COLORS.verified},
    ]}/>
  </Frame>;
};

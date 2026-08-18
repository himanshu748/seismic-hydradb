import {interpolate, spring, useCurrentFrame, useVideoConfig} from "remotion";
import {Brand, Frame, Headline, Kicker, Panel, ease} from "../components";
import {COLORS} from "../constants";

const phaseOpacity = (frame: number, start: number, end: number): number => interpolate(
  frame,
  [start, start + 22, end - 22, end],
  [0, 1, 1, 0],
  {extrapolateLeft: "clamp", extrapolateRight: "clamp"},
);

export const ProofScene: React.FC<{duration: number}> = ({duration}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const brandIn = spring({frame: frame-1270, fps, config: {damping: 18, mass: .7}});
  return <Frame duration={duration} index={7} label="THE RECEIPTS">
    <div style={{position: "absolute", inset: "160px 102px 90px", opacity: phaseOpacity(frame, 0, 245)}}>
      <Kicker tone={COLORS.verified}>Verified against local HydraDB and real MCP transports</Kicker>
      <Headline size={78} style={{marginTop: 26}}>This is working.<br/><span style={{color: COLORS.orange}}>Not a mock.</span></Headline>
      <Panel style={{position: "absolute", right: 0, top: 24, width: 720, height: 480, padding: "54px", borderColor: COLORS.verified, background: "rgba(27,24,21,.98)"}}>
        <div style={{fontFamily: "Seismic Display", fontSize: 112, fontWeight: 700, color: COLORS.verified, letterSpacing: "-.06em", opacity: ease(frame,45), scale: interpolate(ease(frame,45),[0,1],[.82,1])}}>19 / 19</div>
        <div style={{fontFamily: "Seismic Display", fontSize: 34, fontWeight: 700, marginTop: 20}}>tests pass</div>
        <div style={{display: "flex", gap: 12, marginTop: 42}}>
          {["16 FAST", "3 LIVE", "BOLT", "STDIO + HTTP"].map((label,index)=><span key={label} style={{padding: "11px 14px", border: `1px solid ${COLORS.border}`, borderRadius: 7, color: index>1 ? COLORS.orange : COLORS.muted, fontFamily: "Seismic Mono", fontSize: 14, opacity: ease(frame,80+index*18)}}>{label}</span>)}
        </div>
      </Panel>
    </div>

    <div style={{position: "absolute", inset: "160px 102px 90px", opacity: phaseOpacity(frame, 200, 535)}}>
      <Kicker>Self-authored Track 02 smoke</Kicker>
      <Headline size={74} style={{marginTop: 26}}>Every supported result<br/><span style={{color: COLORS.orange}}>carries an exact path.</span></Headline>
      <div style={{display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 18, marginTop: 54}}>
        {[["12", "source-reviewed tasks"], ["10 / 10", "exact paths valid"], ["2 / 2", "correct abstentions"]].map((card,index)=><Panel key={card[1]} style={{padding: "34px", minHeight: 210, opacity: ease(frame,260+index*34), translate: `0 ${interpolate(ease(frame,260+index*34),[0,1],[26,0])}px`}}><div style={{fontFamily: "Seismic Display", fontSize: 64, fontWeight: 700, color: index===2 ? COLORS.verified : COLORS.orange}}>{card[0]}</div><div style={{fontSize: 22, marginTop: 22}}>{card[1]}</div></Panel>)}
      </div>
      <div style={{marginTop: 28, fontFamily: "Seismic Mono", color: COLORS.muted, fontSize: 15}}>TRANSPARENT LOCAL EVALUATION · NOT AN OFFICIAL HACKATHON SCORE</div>
    </div>

    <div style={{position: "absolute", inset: "150px 102px 90px", opacity: phaseOpacity(frame, 485, 865)}}>
      <Kicker>Same tasks, different retrieval primitive</Kicker>
      <Headline size={72} style={{marginTop: 24}}>Graph structure beats<br/><span style={{color: COLORS.orange}}>similarity alone.</span></Headline>
      <div style={{position: "absolute", right: 0, top: 28, width: 820, display: "grid", gap: 24}}>
        <Panel style={{padding: "34px 36px"}}>
          <div style={{display: "flex", justifyContent: "space-between", fontFamily: "Seismic Mono", fontSize: 18}}><strong style={{color: COLORS.verified}}>HYDRADB GRAPH</strong><strong>1.0000 P@K / R@K</strong></div>
          <div style={{height: 22, marginTop: 24, borderRadius: 99, background: COLORS.quiet, overflow: "hidden"}}><div style={{height: "100%", width: `${interpolate(frame,[540,660],[0,100],{extrapolateLeft:"clamp",extrapolateRight:"clamp"})}%`, background: COLORS.verified, borderRadius: 99}} /></div>
          <div style={{marginTop: 16, color: COLORS.muted}}>Directed reachability plus inspectable path proof</div>
        </Panel>
        <Panel style={{padding: "34px 36px"}}>
          <div style={{display: "flex", justifyContent: "space-between", fontFamily: "Seismic Mono", fontSize: 18}}><strong style={{color: COLORS.warning}}>TF-IDF BASELINE</strong><strong>0.1321 P@K / R@K</strong></div>
          <div style={{height: 22, marginTop: 24, borderRadius: 99, background: COLORS.quiet, overflow: "hidden"}}><div style={{height: "100%", width: `${interpolate(frame,[600,700],[0,13.21],{extrapolateLeft:"clamp",extrapolateRight:"clamp"})}%`, background: COLORS.warning, borderRadius: 99}} /></div>
          <div style={{marginTop: 16, color: COLORS.muted}}>Text resemblance without dependency direction</div>
        </Panel>
      </div>
    </div>

    <div style={{position: "absolute", inset: "160px 102px 90px", opacity: phaseOpacity(frame, 815, 1305)}}>
      <Kicker tone={COLORS.verified}>Deterministic real-repo + stress proof</Kicker>
      <Headline size={74} style={{marginTop: 26}}>The exact target survives<br/><span style={{color: COLORS.orange}}>real and larger graphs.</span></Headline>
      <div style={{display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16, marginTop: 58}}>
        {[["5,000", "artifacts"], ["20,000", "relationships"], ["25 / 25", "exact recoveries"], ["8.926 ms", "query p95"]].map((card,index)=><Panel key={card[1]} style={{padding: "32px 28px", minHeight: 205, opacity: ease(frame,870+index*34), translate: `0 ${interpolate(ease(frame,870+index*34),[0,1],[28,0])}px`}}><div style={{fontFamily: "Seismic Display", fontSize: index===3 ? 48 : 57, fontWeight: 700, color: index===2 ? COLORS.verified : COLORS.orange}}>{card[0]}</div><div style={{fontSize: 21, marginTop: 20}}>{card[1]}</div></Panel>)}
      </div>
      <div style={{marginTop: 28, fontFamily: "Seismic Mono", color: COLORS.verified, fontSize: 16, opacity: ease(frame,1015)}}>3 REAL REPOS · 49 SUPPORTED IMPACTS · EVERY RETURNED PATH VALID</div>
    </div>

    <div style={{position: "absolute", inset: 0, background: COLORS.paper, color: COLORS.graphite, display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 118px", translate: `0 ${interpolate(frame,[1268,1288],[1080,0],{extrapolateLeft:"clamp",extrapolateRight:"clamp"})}px`}}>
      <div style={{scale: brandIn}}><Brand large /></div>
      <div style={{maxWidth: 940, textAlign: "right", opacity: brandIn}}><div style={{fontFamily: "Seismic Display", fontSize: 62, lineHeight: 1.02, fontWeight: 700, letterSpacing: "-.05em"}}>Know what a code change can break<br/>before the agent edits it.</div><div style={{fontFamily: "Seismic Mono", color: "#5d554e", marginTop: 28, fontSize: 20}}>github.com/himanshu748/seismic-hydradb</div></div>
    </div>
  </Frame>;
};

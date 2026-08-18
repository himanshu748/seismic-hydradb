import {interpolate, useCurrentFrame} from "remotion";
import {COLORS} from "../constants";
import {Frame, Headline, Kicker, Reveal, Sheet, Status, ease} from "../components";

export const AbstentionScene: React.FC<{duration: number}> = ({duration}) => {
  const frame = useCurrentFrame();
  const sweep = interpolate(frame, [42, 188], [0, 100], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
  return <Frame duration={duration} index={4} label="THE HONEST ZERO" mode="paper">
    <div style={{position: "absolute", inset: 0, display: "grid", gridTemplateColumns: "1fr 710px", gap: 70, alignItems: "center"}}>
      <div style={{paddingLeft: 26}}>
        <Reveal at={6}>
          <Kicker dark>Unsupported target · explicit abstention</Kicker>
          <Headline size={102} style={{marginTop: 28}}>Zero is a<br/><span style={{color: COLORS.verified}}>valid answer.</span></Headline>
          <div style={{fontSize: 26, lineHeight: 1.45, color: "#6f665f", maxWidth: 710, marginTop: 38}}>When HydraDB has no path, Seismic returns no impact claim. The agent sees the boundary instead of a confident guess.</div>
        </Reveal>
        <Reveal at={220} from="left" style={{marginTop: 42}}><Status tone="green">NO PATH → NO CLAIM</Status></Reveal>
      </div>
      <Reveal at={28} from="right">
        <Sheet mode="paper" style={{height: 660, padding: "34px", position: "relative", overflow: "hidden"}}>
          <div style={{display: "flex", justifyContent: "space-between", fontFamily: "Seismic Mono", fontSize: 13, color: "#70665e"}}><span>GRAPH QUERY RECEIPT</span><span>04 / ABSTAIN</span></div>
          <div style={{marginTop: 40, padding: "22px", borderRadius: 12, background: COLORS.graphite, color: COLORS.paper, fontFamily: "Seismic Mono", fontSize: 16, lineHeight: 1.7}}>
            <div style={{color: COLORS.muted}}>&gt; analyze_change</div>
            <div style={{marginTop: 6}}>server.py::<span style={{color: COLORS.orange}}>not_real</span></div>
            <div style={{height: 3, background: COLORS.border, marginTop: 22, position: "relative", overflow: "hidden"}}><div style={{height: "100%", width: `${sweep}%`, background: COLORS.orange}} /></div>
          </div>
          <div style={{fontFamily: "Seismic Display", fontSize: 210, lineHeight: .8, fontWeight: 700, letterSpacing: "-.08em", marginTop: 58, color: COLORS.graphite, opacity: ease(frame, 130)}}>0</div>
          <div style={{position: "absolute", left: 300, top: 330, right: 34}}>
            {[["resolved targets", "0"], ["supported paths", "0"], ["invented claims", "0"]].map((item, index) => <div key={item[0]} style={{display: "flex", justifyContent: "space-between", padding: "17px 0", borderBottom: "1px solid rgba(18,16,14,.14)", fontFamily: "Seismic Mono", fontSize: 15, opacity: ease(frame, 160 + index * 32)}}><span style={{color: "#70665e"}}>{item[0]}</span><strong style={{color: index === 2 ? COLORS.verified : COLORS.graphite}}>{item[1]}</strong></div>)}
          </div>
          <div style={{position: "absolute", left: 34, right: 34, bottom: 32, paddingTop: 18, borderTop: "2px solid rgba(18,16,14,.15)", display: "flex", justifyContent: "space-between", fontFamily: "Seismic Mono", color: COLORS.verified, opacity: ease(frame, 248)}}><span>ABSTAINED</span><span>BOUNDARY EXPOSED ✓</span></div>
        </Sheet>
      </Reveal>
    </div>
  </Frame>;
};

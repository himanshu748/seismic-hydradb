import {interpolate, spring, useCurrentFrame, useVideoConfig} from "remotion";
import {Brand, Frame, Headline, Kicker, Panel, ease} from "../components";
import {COLORS} from "../constants";

const cards = [
  ["16 / 16", "tests pass", "13 fast · 3 live"],
  ["10 / 10", "exact paths", "self-authored smoke"],
  ["2 / 2", "abstentions", "unsupported cases"],
  ["25 / 25", "stress targets", "5k nodes · 20k edges"],
];

export const ProofScene: React.FC<{duration: number}> = ({duration}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const brandIn = spring({frame: frame-220, fps, config: {damping: 18, mass: .7}});
  return <Frame duration={duration} index={7} label="THE RECEIPTS">
    <div style={{position: "absolute", left: 102, right: 102, top: 166}}>
      <Kicker tone={COLORS.verified}>Verified against local HydraDB and real MCP transports</Kicker>
      <Headline size={78} style={{marginTop: 26}}>Working product.<br/><span style={{color: COLORS.orange}}>Bounded claims.</span></Headline>
      <div style={{display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16, marginTop: 48}}>{cards.map((card,index)=><Panel key={card[0]} style={{padding: "30px 28px", minHeight: 210, opacity: ease(frame,55+index*20), translate: `0 ${interpolate(ease(frame,55+index*20),[0,1],[28,0])}px`}}><div style={{fontFamily: "Seismic Display", fontSize: 56, fontWeight: 700, color: index===0 ? COLORS.verified : COLORS.orange}}>{card[0]}</div><div style={{fontSize: 22, marginTop: 18}}>{card[1]}</div><div style={{fontFamily: "Seismic Mono", color: COLORS.muted, fontSize: 14, marginTop: 11}}>{card[2]}</div></Panel>)}</div>
      <div style={{marginTop: 32, fontFamily: "Seismic Mono", fontSize: 15, color: COLORS.muted, opacity: ease(frame,148)}}>SELF-AUTHORED TRACK 02 SMOKE · LOCAL DETERMINISTIC STRESS · NOT AN OFFICIAL SCORE</div>
    </div>
    <div style={{position: "absolute", left: 0, right: 0, bottom: 0, height: 320, background: COLORS.paper, color: COLORS.graphite, display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 110px", opacity: ease(frame,205)}}>
      <div style={{scale: brandIn}}><Brand large /></div>
      <div style={{maxWidth: 870, textAlign: "right", opacity: brandIn}}><div style={{fontFamily: "Seismic Display", fontSize: 50, fontWeight: 700, letterSpacing: "-.04em"}}>Know what a code change can break<br/>before the agent edits it.</div><div style={{fontFamily: "Seismic Mono", color: "#5d554e", marginTop: 20, fontSize: 17}}>github.com/himanshu748/seismic-hydradb</div></div>
    </div>
  </Frame>;
};

import {interpolate, spring, useCurrentFrame, useVideoConfig} from "remotion";
import {Brand, CountUp, Frame, Kicker, Reveal, Status} from "../components";
import {COLORS} from "../constants";

const phase = (frame: number, start: number, end: number): number => interpolate(
  frame,
  [start, start + 18, end - 18, end],
  [0, 1, 1, 0],
  {extrapolateLeft: "clamp", extrapolateRight: "clamp"},
);

const RepoRow: React.FC<{name: string; impacts: number; at: number}> = ({name, impacts, at}) => {
  const frame = useCurrentFrame();
  const width = interpolate(frame, [at, at + 55], [0, impacts / 20 * 100], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
  return <div style={{display: "grid", gridTemplateColumns: "190px 1fr 80px", gap: 24, alignItems: "center", marginTop: 24, opacity: phase(frame, at, 1300)}}>
    <div style={{fontFamily: "Seismic Mono", fontSize: 18}}>{name}</div>
    <div style={{height: 22, background: "rgba(18,16,14,.13)", borderRadius: 99, overflow: "hidden"}}><div style={{height: "100%", width: `${width}%`, background: COLORS.orange, borderRadius: 99}} /></div>
    <div style={{fontFamily: "Seismic Display", fontSize: 36, fontWeight: 700}}>{impacts}</div>
  </div>;
};

export const ProofScene: React.FC<{duration: number}> = ({duration}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const close = spring({frame: frame - 1275, fps, config: {damping: 18, mass: .72}});
  const graphBar = interpolate(frame, [580, 680], [0, 100], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
  const textBar = interpolate(frame, [630, 710], [0, 13.21], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
  return <Frame duration={duration} index={7} label="THE RECEIPT WALL" mode="dark">
    <div style={{position: "absolute", inset: 0}}>
      <div style={{position: "absolute", inset: 0, opacity: phase(frame, 0, 260), display: "grid", gridTemplateColumns: "1.25fr .75fr", alignItems: "center"}}>
        <div>
          <Kicker tone={COLORS.verified}>Verified locally against real HydraDB and MCP</Kicker>
          <div style={{fontFamily: "Seismic Display", fontSize: 250, lineHeight: .75, letterSpacing: "-.09em", fontWeight: 700, marginTop: 72, color: COLORS.orange}}><CountUp value={19} at={35} /></div>
          <div style={{fontFamily: "Seismic Display", fontSize: 58, fontWeight: 700, letterSpacing: "-.05em", marginTop: 38}}>tests pass. Product works.</div>
        </div>
        <div style={{borderLeft: `1px solid ${COLORS.border}`, paddingLeft: 62, display: "grid", gap: 22}}>
          {[["16", "FAST"], ["3", "LIVE"], ["BOLT", "DATABASE"], ["2", "MCP TRANSPORTS"]].map((item, index) => <Reveal key={item[1]} at={68 + index * 28} from="right"><div style={{display: "flex", alignItems: "baseline", justifyContent: "space-between", paddingBottom: 20, borderBottom: `1px solid ${COLORS.border}`}}><strong style={{fontFamily: "Seismic Display", fontSize: 48, color: index < 2 ? COLORS.paper : COLORS.verified}}>{item[0]}</strong><span style={{fontFamily: "Seismic Mono", fontSize: 14, color: COLORS.muted}}>{item[1]}</span></div></Reveal>)}
        </div>
      </div>

      <div style={{position: "absolute", inset: 0, opacity: phase(frame, 220, 545), display: "grid", gridTemplateRows: "auto 1fr", paddingTop: 42}}>
        <div style={{display: "flex", justifyContent: "space-between", alignItems: "center"}}><Kicker>Source-reviewed Track 02 smoke</Kicker><Status tone="green">NO UNSUPPORTED CLAIMS</Status></div>
        <div style={{display: "grid", gridTemplateColumns: "1fr 1fr", gap: 120, alignItems: "center"}}>
          <div><div style={{fontFamily: "Seismic Display", fontSize: 190, color: COLORS.orange, fontWeight: 700, letterSpacing: "-.08em"}}>10/10</div><div style={{fontFamily: "Seismic Display", fontSize: 42, fontWeight: 700}}>supported tasks<br/>carry exact paths</div></div>
          <div><div style={{fontFamily: "Seismic Display", fontSize: 190, color: COLORS.verified, fontWeight: 700, letterSpacing: "-.08em"}}>2/2</div><div style={{fontFamily: "Seismic Display", fontSize: 42, fontWeight: 700}}>unsupported tasks<br/>abstain correctly</div></div>
        </div>
        <div style={{position: "absolute", left: 0, bottom: 16, fontFamily: "Seismic Mono", color: COLORS.muted, fontSize: 13}}>SELF-AUTHORED SMOKE · NOT AN OFFICIAL HACKATHON SCORE</div>
      </div>

      <div style={{position: "absolute", inset: 0, opacity: phase(frame, 500, 865), paddingTop: 40}}>
        <Kicker>Same tasks · different retrieval primitive</Kicker>
        <div style={{fontFamily: "Seismic Display", fontSize: 74, lineHeight: .98, letterSpacing: "-.06em", fontWeight: 700, marginTop: 24}}>Graph direction wins.<br/><span style={{color: COLORS.orange}}>Resemblance alone does not.</span></div>
        <div style={{marginTop: 70}}>
          <div style={{display: "grid", gridTemplateColumns: "240px 1fr 190px", gap: 30, alignItems: "center"}}>
            <strong style={{fontFamily: "Seismic Mono", color: COLORS.verified}}>HYDRADB GRAPH</strong>
            <div style={{height: 58, background: COLORS.quiet, borderRadius: 99, overflow: "hidden"}}><div style={{height: "100%", width: `${graphBar}%`, background: COLORS.verified}} /></div>
            <strong style={{fontFamily: "Seismic Display", fontSize: 45}}>1.0000</strong>
          </div>
          <div style={{display: "grid", gridTemplateColumns: "240px 1fr 190px", gap: 30, alignItems: "center", marginTop: 34}}>
            <strong style={{fontFamily: "Seismic Mono", color: COLORS.warning}}>TF-IDF</strong>
            <div style={{height: 58, background: COLORS.quiet, borderRadius: 99, overflow: "hidden"}}><div style={{height: "100%", width: `${textBar}%`, background: COLORS.warning}} /></div>
            <strong style={{fontFamily: "Seismic Display", fontSize: 45}}>0.1321</strong>
          </div>
        </div>
        <div style={{position: "absolute", left: 0, bottom: 38, display: "flex", gap: 40, fontFamily: "Seismic Mono", color: COLORS.muted, fontSize: 14}}><span>PRECISION@K</span><span>RECALL@K</span><span>IDENTICAL TASKS</span></div>
      </div>

      <div style={{position: "absolute", inset: -1, opacity: phase(frame, 820, 1305), background: COLORS.paper, color: COLORS.graphite, padding: "46px 50px"}}>
        <div style={{display: "flex", justifyContent: "space-between", alignItems: "center"}}><Kicker dark>Portability, then scale</Kicker><Status tone="ink">DETERMINISTIC TARGET RULE</Status></div>
        <div style={{fontFamily: "Seismic Display", fontSize: 72, lineHeight: .98, letterSpacing: "-.06em", fontWeight: 700, marginTop: 28}}>Three real repos.<br/><span style={{color: COLORS.orange}}>Forty-nine valid impacts.</span></div>
        <div style={{display: "grid", gridTemplateColumns: "1.05fr .95fr", gap: 72, marginTop: 45}}>
          <div><RepoRow name="HydraMind" impacts={14} at={900}/><RepoRow name="OmniDev" impacts={15} at={950}/><RepoRow name="BlastRadius" impacts={20} at={1000}/></div>
          <div style={{borderLeft: "1px solid rgba(18,16,14,.16)", paddingLeft: 62, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 18}}>
            {[["5,000", "ARTIFACTS"], ["20,000", "RELATIONSHIPS"], ["25/25", "EXACT RECOVERIES"], ["8.926 ms", "QUERY P95"]].map((item, index) => <Reveal key={item[1]} at={930 + index * 38} from="up"><div style={{padding: "24px 0", borderTop: "2px solid rgba(18,16,14,.14)"}}><div style={{fontFamily: "Seismic Display", fontSize: index === 3 ? 45 : 54, fontWeight: 700, color: index === 2 ? COLORS.verified : COLORS.graphite}}>{item[0]}</div><div style={{fontFamily: "Seismic Mono", fontSize: 12, marginTop: 12, color: "#6f665f"}}>{item[1]}</div></div></Reveal>)}
          </div>
        </div>
        <div style={{position: "absolute", left: 50, bottom: 38, fontFamily: "Seismic Mono", color: COLORS.verified, fontSize: 14}}>EVERY RETURNED REAL-REPOSITORY PATH PASSED STRUCTURAL VALIDATION ✓</div>
      </div>

      <div style={{position: "absolute", inset: -1, background: COLORS.orange, color: COLORS.graphite, display: "grid", gridTemplateColumns: ".8fr 1.2fr", alignItems: "center", padding: "0 82px", transform: `translateY(${interpolate(frame, [1265, 1290], [940, 0], {extrapolateLeft: "clamp", extrapolateRight: "clamp"})}px)`}}>
        <div style={{transform: `scale(${close})`, opacity: close}}><Brand large dark /></div>
        <div style={{textAlign: "right", opacity: close}}>
          <div style={{fontFamily: "Seismic Display", fontSize: 70, lineHeight: .94, letterSpacing: "-.065em", fontWeight: 700}}>Know what the patch can break<br/>before the agent edits.</div>
          <div style={{fontFamily: "Seismic Mono", fontSize: 18, marginTop: 34}}>github.com/himanshu748/seismic-hydradb</div>
        </div>
      </div>
    </div>
  </Frame>;
};

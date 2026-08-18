import {interpolate, useCurrentFrame} from "remotion";
import {COLORS} from "../constants";
import {Frame, Headline, Kicker, Reveal, Sheet, Status, ease} from "../components";

const procedures = [
  ["algo.SSpaths", "one changed target", "BLAST RADIUS"],
  ["algo.MSpaths", "multiple changes", "UNIFIED IMPACT"],
  ["algo.SPpaths", "one result", "EXACT PROOF"],
];

export const NativeGraphScene: React.FC<{duration: number}> = ({duration}) => {
  const frame = useCurrentFrame();
  const sever = ease(frame, 610, 26);
  return <Frame duration={duration} index={6} label="WHY HYDRADB IS ESSENTIAL" mode="paper">
    <div style={{position: "absolute", inset: 0, display: "grid", gridTemplateColumns: "610px 1fr", gap: 54, paddingTop: 32}}>
      <div>
        <Reveal at={5}><Kicker dark>System of record + path engine</Kicker><Headline size={86} style={{marginTop: 25}}>HydraDB is not<br/><span style={{color: COLORS.orange}}>a log sink.</span></Headline></Reveal>
        <Reveal at={62} from="left">
          <div style={{fontSize: 25, color: "#6f665f", lineHeight: 1.46, marginTop: 38}}>Immutable snapshots, stable artifact identities, typed relationships and incident evidence live in one graph.</div>
        </Reveal>
        <div style={{marginTop: 44, display: "grid", gap: 13}}>{procedures.map((item, index) => <Reveal key={item[0]} at={105 + index * 48} from="left"><Sheet mode="paper" style={{padding: "19px 22px", display: "grid", gridTemplateColumns: "180px 1fr", alignItems: "center", background: index === 0 ? "rgba(255,90,36,.08)" : "rgba(255,255,255,.48)"}}><strong style={{fontFamily: "Seismic Mono", color: COLORS.orange}}>{item[0]}</strong><span style={{fontSize: 17}}>{item[1]}</span></Sheet></Reveal>)}</div>
      </div>
      <Reveal at={34} from="right">
        <Sheet mode="paper" style={{height: 760, position: "relative", overflow: "hidden", background: "rgba(255,255,255,.62)"}}>
          <div style={{position: "absolute", left: "50%", top: 55, bottom: 55, width: 230, marginLeft: -115, borderRadius: 120, background: COLORS.graphite, color: COLORS.paper, display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", textAlign: "center", transform: `scaleX(${1 - sever * .96})`, opacity: 1-sever*.75}}>
            <div style={{width: 118, height: 118, borderRadius: 99, background: COLORS.orange, display: "grid", placeItems: "center", color: COLORS.graphite, fontFamily: "Seismic Display", fontWeight: 700, fontSize: 29}}>HydraDB</div>
            <div style={{fontFamily: "Seismic Mono", fontSize: 11, letterSpacing: ".14em", marginTop: 28, color: COLORS.muted}}>BOLT / OPENCYPHER</div>
          </div>
          {procedures.map((item, index) => {
            const y = 130 + index * 205;
            return <div key={item[0]} style={{position: "absolute", left: 50, right: 50, top: y, display: "grid", gridTemplateColumns: "1fr 270px 1fr", alignItems: "center", opacity: ease(frame, 150 + index * 55) * (1-sever)}}>
              <div style={{fontFamily: "Seismic Mono", fontSize: 16, textAlign: "right", paddingRight: 35}}>{item[0]}</div>
              <div style={{height: 2, background: COLORS.orange, position: "relative"}}><span style={{position: "absolute", left: "50%", top: -7, width: 16, height: 16, borderRadius: 99, background: COLORS.orange}} /></div>
              <div style={{fontFamily: "Seismic Mono", fontSize: 13, letterSpacing: ".12em", paddingLeft: 35, color: COLORS.verified}}>{item[2]}</div>
            </div>;
          })}
          <div style={{position: "absolute", left: 42, right: 42, bottom: 34, display: "flex", justifyContent: "space-between", opacity: ease(frame, 390) * (1-sever)}}>
            <Status tone="ink">IMMUTABLE SNAPSHOTS</Status><Status tone="green">INCIDENT MEMORY</Status><Status tone="ink">EXACT PATHS</Status>
          </div>
          <div style={{position: "absolute", inset: 0, background: COLORS.orange, display: "grid", placeItems: "center", opacity: sever}}>
            <div style={{textAlign: "center", transform: `scale(${interpolate(sever, [0, 1], [.78, 1])})`}}>
              <div style={{fontFamily: "Seismic Mono", fontSize: 15, letterSpacing: ".17em"}}>REMOVE HYDRADB</div>
              <div style={{fontFamily: "Seismic Display", fontSize: 72, fontWeight: 700, letterSpacing: "-.06em", marginTop: 20}}>No direction.<br/>No reachability.<br/>No proof.</div>
            </div>
          </div>
        </Sheet>
      </Reveal>
    </div>
  </Frame>;
};

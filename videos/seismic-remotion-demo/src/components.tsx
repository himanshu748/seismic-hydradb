import type {CSSProperties, ReactNode} from "react";
import {interpolate, spring, useCurrentFrame, useVideoConfig} from "remotion";
import {COLORS} from "./constants";

export const ease = (frame: number, at: number, duration = 22): number => interpolate(frame, [at, at + duration], [0, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
export const sceneFade = (frame: number, duration: number): number => interpolate(frame, [0, 16, duration - 14, duration], [0, 1, 1, 0], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});

export const Frame: React.FC<{children: ReactNode; duration: number; index: number; label: string}> = ({children, duration, index, label}) => {
  const frame = useCurrentFrame();
  const driftX = Math.sin(frame / 72) * 3.5;
  const driftY = Math.cos(frame / 94) * 2.5;
  const driftScale = 1.004 + Math.sin(frame / 118) * 0.0025;
  const glowX = 46 + Math.sin(frame / 86) * 24;
  const glowY = 42 + Math.cos(frame / 111) * 18;
  return (
    <div style={{position: "absolute", inset: 0, overflow: "hidden", background: COLORS.graphite, color: COLORS.paper, opacity: sceneFade(frame, duration), fontFamily: "Seismic Sans"}}>
      <SurveyGrid frame={frame} />
      <div style={{position: "absolute", inset: -180, background: `radial-gradient(circle at ${glowX}% ${glowY}%, rgba(255,90,36,.065), transparent 34%)`, filter: "blur(20px)", opacity: 0.72}} />
      <div style={{position: "absolute", inset: 0, zIndex: 1, transform: `translate3d(${driftX}px, ${driftY}px, 0) scale(${driftScale})`, transformOrigin: "50% 48%"}}>{children}</div>
      <div style={{position: "absolute", left: 86, top: 48, width: 1748, height: 48, display: "flex", alignItems: "center", justifyContent: "space-between", zIndex: 1000}}>
        <Brand />
        <div style={{display: "flex", gap: 18, alignItems: "center", fontFamily: "Seismic Mono", fontSize: 15, letterSpacing: "0.12em", color: COLORS.muted}}>
          <span>{label}</span><span style={{color: COLORS.orange}}>{String(index).padStart(2, "0")} / 07</span>
        </div>
      </div>
      <div style={{position: "absolute", left: 0, bottom: 0, zIndex: 1000, height: 5, width: `${((index - 1 + frame / duration) / 7) * 100}%`, background: COLORS.orange, boxShadow: "0 0 22px rgba(255,90,36,.42)"}} />
    </div>
  );
};

export const SurveyGrid: React.FC<{frame: number}> = ({frame}) => (
  <div style={{position: "absolute", inset: -64, backgroundImage: "linear-gradient(rgba(245,239,230,.038) 1px, transparent 1px),linear-gradient(90deg, rgba(245,239,230,.038) 1px, transparent 1px)", backgroundPosition: `${frame * 0.16}px ${frame * 0.1}px`, backgroundSize: "64px 64px", maskImage: "linear-gradient(to bottom, #000 0%, rgba(0,0,0,.45) 75%, transparent 100%)"}} />
);

export const Brand: React.FC<{large?: boolean}> = ({large = false}) => (
  <div style={{display: "flex", alignItems: "center", gap: large ? 22 : 12}}>
    <FaultMark size={large ? 70 : 38} />
    <span style={{fontFamily: "Seismic Display", fontSize: large ? 56 : 28, fontWeight: 700, letterSpacing: "-0.045em"}}>Seismic</span>
  </div>
);

export const FaultMark: React.FC<{size: number}> = ({size}) => (
  <svg width={size} height={size} viewBox="0 0 64 64" aria-hidden="true">
    <rect x="2" y="2" width="60" height="60" rx="9" fill={COLORS.orange} />
    <path d="M8 35h15l5-18 8 31 6-20 5 7h9" fill="none" stroke={COLORS.graphite} strokeWidth="5" strokeLinejoin="round" />
  </svg>
);

export const Headline: React.FC<{children: ReactNode; style?: CSSProperties; size?: number}> = ({children, style, size = 94}) => (
  <div style={{fontFamily: "Seismic Display", fontSize: size, fontWeight: 700, lineHeight: 0.98, letterSpacing: "-0.055em", maxWidth: 1180, ...style}}>{children}</div>
);

export const Kicker: React.FC<{children: ReactNode; tone?: string}> = ({children, tone = COLORS.orange}) => (
  <div style={{fontFamily: "Seismic Mono", fontSize: 18, lineHeight: 1, letterSpacing: "0.15em", color: tone, textTransform: "uppercase"}}>{children}</div>
);

export const Panel: React.FC<{children: ReactNode; style?: CSSProperties}> = ({children, style}) => (
  <div style={{background: "rgba(27,24,21,.96)", border: `1px solid ${COLORS.border}`, borderRadius: 10, boxShadow: "0 28px 80px rgba(0,0,0,.28)", ...style}}>{children}</div>
);

export const Node: React.FC<{x: number; y: number; label: string; kind: string; active?: boolean; delay?: number; style?: CSSProperties}> = ({x, y, label, kind, active = false, delay = 0, style}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const scale = spring({frame: frame - delay, fps, config: {damping: 18, mass: 0.65}});
  const pulse = 0.5 + Math.sin(frame / 18) * 0.5;
  return (
    <div style={{position: "absolute", left: x, top: y, width: 214, height: 88, padding: "15px 17px", borderRadius: 8, border: `1px solid ${active ? COLORS.orange : COLORS.border}`, background: active ? "#2b1c15" : COLORS.quiet, boxShadow: active ? `0 0 0 1px rgba(255,90,36,.2), 0 0 ${28 + pulse * 18}px rgba(255,90,36,${0.1 + pulse * 0.08})` : "none", scale, ...style}}>
      <div style={{fontFamily: "Seismic Mono", fontSize: 13, letterSpacing: "0.1em", color: active ? COLORS.orange : COLORS.muted}}>{kind}</div>
      <div style={{fontFamily: "Seismic Mono", fontWeight: 600, fontSize: 20, marginTop: 10, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis"}}>{label}</div>
    </div>
  );
};

export const Edge: React.FC<{x1: number; y1: number; x2: number; y2: number; label: string; active?: boolean; delay?: number}> = ({x1, y1, x2, y2, label, active = false, delay = 0}) => {
  const frame = useCurrentFrame();
  const progress = ease(frame, delay, 30);
  const length = Math.hypot(x2 - x1, y2 - y1);
  const angle = Math.atan2(y2 - y1, x2 - x1) * 180 / Math.PI;
  return <>
    <div style={{position: "absolute", left: x1, top: y1, width: length, height: 2, transformOrigin: "left center", rotate: `${angle}deg`, background: active ? COLORS.orange : COLORS.border, scale: `${progress} 1`}} />
    <div style={{position: "absolute", left: (x1 + x2) / 2 - 40, top: (y1 + y2) / 2 - 24, padding: "4px 8px", background: COLORS.graphite, fontFamily: "Seismic Mono", fontSize: 12, letterSpacing: ".08em", color: active ? COLORS.orange : COLORS.muted, opacity: progress}}>{label}</div>
  </>;
};

export const Terminal: React.FC<{lines: Array<{text: string; tone?: string}>; revealAt?: number; style?: CSSProperties}> = ({lines, revealAt = 0, style}) => {
  const frame = useCurrentFrame();
  return <Panel style={{overflow: "hidden", ...style}}>
    <div style={{height: 44, borderBottom: `1px solid ${COLORS.border}`, display: "flex", alignItems: "center", gap: 8, padding: "0 16px"}}>
      {[COLORS.critical, COLORS.warning, COLORS.verified].map((color) => <span key={color} style={{width: 9, height: 9, borderRadius: 99, background: color}} />)}
      <span style={{marginLeft: 10, color: COLORS.muted, fontFamily: "Seismic Mono", fontSize: 13}}>agent / seismic</span>
    </div>
    <div style={{padding: "24px 28px", fontFamily: "Seismic Mono", fontSize: 18, lineHeight: 1.8}}>
      {lines.map((line, index) => <div key={`${index}-${line.text}`} style={{color: line.tone ?? COLORS.paper, opacity: ease(frame, revealAt + index * 17, 12), translate: `${interpolate(ease(frame, revealAt + index * 17, 12), [0,1], [12,0])}px 0`}}>{line.text}</div>)}
    </div>
  </Panel>;
};

import type {CSSProperties, ReactNode} from "react";
import {interpolate, spring, useCurrentFrame, useVideoConfig} from "remotion";
import {COLORS} from "./constants";

export type FrameMode = "dark" | "paper" | "orange";

export const ease = (frame: number, at: number, duration = 22): number => interpolate(
  frame,
  [at, at + duration],
  [0, 1],
  {extrapolateLeft: "clamp", extrapolateRight: "clamp"},
);

const palette = (mode: FrameMode) => {
  if (mode === "paper") {
    return {background: COLORS.paper, foreground: COLORS.graphite, muted: "#6f665f", line: "rgba(18,16,14,.13)"};
  }
  if (mode === "orange") {
    return {background: COLORS.orange, foreground: COLORS.graphite, muted: "#58210f", line: "rgba(18,16,14,.18)"};
  }
  return {background: COLORS.graphite, foreground: COLORS.paper, muted: COLORS.muted, line: "rgba(245,239,230,.12)"};
};

export const Frame: React.FC<{
  children: ReactNode;
  duration: number;
  index: number;
  label: string;
  mode?: FrameMode;
}> = ({children, duration, index, label, mode = "dark"}) => {
  const frame = useCurrentFrame();
  const colors = palette(mode);
  const enter = ease(frame, 0, 12);
  const exit = interpolate(frame, [Math.max(0, duration - 12), duration - 1], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const scan = ((frame * 2.2) % 2200) - 220;
  const grid = mode === "dark" ? "rgba(245,239,230,.035)" : "rgba(18,16,14,.045)";
  return (
    <div style={{position: "absolute", inset: 0, overflow: "hidden", background: colors.background, color: colors.foreground, fontFamily: "Seismic Sans", opacity: Math.min(enter, exit)}}>
      <div style={{position: "absolute", inset: 0, backgroundImage: `linear-gradient(${grid} 1px, transparent 1px), linear-gradient(90deg, ${grid} 1px, transparent 1px)`, backgroundSize: "72px 72px", backgroundPosition: `${frame * 0.12}px ${frame * 0.07}px`, opacity: .72}} />
      <div style={{position: "absolute", top: 0, bottom: 0, left: scan, width: 280, background: mode === "dark" ? "linear-gradient(90deg, transparent, rgba(255,90,36,.05), transparent)" : "linear-gradient(90deg, transparent, rgba(18,16,14,.035), transparent)"}} />
      <div style={{position: "absolute", left: 42, top: 34, bottom: 34, width: 72, borderRight: `1px solid ${colors.line}`, display: "flex", flexDirection: "column", justifyContent: "space-between", alignItems: "flex-start", zIndex: 10}}>
        <FaultMark size={42} inverted={mode === "orange"} />
        <div style={{writingMode: "vertical-rl", rotate: "180deg", fontFamily: "Seismic Mono", fontSize: 13, letterSpacing: ".18em", color: colors.muted}}>{label}</div>
        <div style={{fontFamily: "Seismic Mono", fontSize: 17, fontWeight: 700}}>{String(index).padStart(2, "0")}</div>
      </div>
      <div style={{position: "absolute", left: 144, right: 58, top: 34, height: 46, display: "flex", alignItems: "center", justifyContent: "space-between", borderBottom: `1px solid ${colors.line}`, zIndex: 10}}>
        <span style={{fontFamily: "Seismic Display", fontSize: 23, fontWeight: 700, letterSpacing: "-.04em"}}>Seismic / proof before the patch</span>
        <span style={{fontFamily: "Seismic Mono", fontSize: 12, letterSpacing: ".14em", color: colors.muted}}>HACK HYDRA · TRACK 02B · {String(index).padStart(2, "0")}/07</span>
      </div>
      <div style={{position: "absolute", inset: "92px 58px 34px 144px", zIndex: 2}}>{children}</div>
      <div style={{position: "absolute", left: 0, bottom: 0, height: 7, width: `${((index - 1 + frame / duration) / 7) * 100}%`, background: mode === "orange" ? COLORS.graphite : COLORS.orange}} />
    </div>
  );
};

export const FaultMark: React.FC<{size: number; inverted?: boolean}> = ({size, inverted = false}) => (
  <svg width={size} height={size} viewBox="0 0 64 64" aria-hidden="true">
    <rect x="2" y="2" width="60" height="60" rx="10" fill={inverted ? COLORS.graphite : COLORS.orange} />
    <path d="M8 35h15l5-18 8 31 6-20 5 7h9" fill="none" stroke={inverted ? COLORS.orange : COLORS.graphite} strokeWidth="5" strokeLinejoin="round" />
  </svg>
);

export const Brand: React.FC<{large?: boolean; dark?: boolean}> = ({large = false, dark = false}) => (
  <div style={{display: "flex", alignItems: "center", gap: large ? 24 : 12, color: dark ? COLORS.graphite : "inherit"}}>
    <FaultMark size={large ? 78 : 40} inverted={dark} />
    <span style={{fontFamily: "Seismic Display", fontSize: large ? 64 : 28, fontWeight: 700, letterSpacing: "-.05em"}}>Seismic</span>
  </div>
);

export const Headline: React.FC<{children: ReactNode; style?: CSSProperties; size?: number}> = ({children, style, size = 100}) => (
  <div style={{fontFamily: "Seismic Display", fontSize: size, fontWeight: 700, lineHeight: .94, letterSpacing: "-.065em", ...style}}>{children}</div>
);

export const Kicker: React.FC<{children: ReactNode; tone?: string; dark?: boolean}> = ({children, tone, dark = false}) => (
  <div style={{fontFamily: "Seismic Mono", fontSize: 16, lineHeight: 1, letterSpacing: ".16em", color: tone ?? (dark ? "#6f665f" : COLORS.orange), textTransform: "uppercase"}}>{children}</div>
);

export const Sheet: React.FC<{children: ReactNode; style?: CSSProperties; mode?: FrameMode}> = ({children, style, mode = "dark"}) => {
  const colors = palette(mode);
  return <div style={{background: mode === "dark" ? "rgba(28,24,21,.92)" : "rgba(255,255,255,.52)", border: `1px solid ${colors.line}`, borderRadius: 16, boxShadow: mode === "dark" ? "0 28px 100px rgba(0,0,0,.25)" : "0 26px 90px rgba(61,42,29,.09)", ...style}}>{children}</div>;
};

export const Reveal: React.FC<{children: ReactNode; at: number; style?: CSSProperties; from?: "up" | "left" | "right" | "scale"}> = ({children, at, style, from = "up"}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const value = spring({frame: frame - at, fps, config: {damping: 19, mass: .68, stiffness: 120}});
  const transforms: Record<string, string> = {
    up: `translateY(${interpolate(value, [0, 1], [34, 0])}px)`,
    left: `translateX(${interpolate(value, [0, 1], [-42, 0])}px)`,
    right: `translateX(${interpolate(value, [0, 1], [42, 0])}px)`,
    scale: `scale(${interpolate(value, [0, 1], [.78, 1])})`,
  };
  return <div style={{opacity: value, transform: transforms[from], ...style}}>{children}</div>;
};

export const Status: React.FC<{children: ReactNode; tone?: "orange" | "green" | "yellow" | "ink"; style?: CSSProperties}> = ({children, tone = "orange", style}) => {
  const toneMap = {orange: COLORS.orange, green: COLORS.verified, yellow: COLORS.warning, ink: COLORS.graphite};
  const color = toneMap[tone];
  return <span style={{display: "inline-flex", alignItems: "center", gap: 9, padding: "10px 14px", border: `1px solid ${color}`, borderRadius: 999, color, fontFamily: "Seismic Mono", fontSize: 13, letterSpacing: ".08em", ...style}}><span style={{width: 7, height: 7, borderRadius: 99, background: color}} />{children}</span>;
};

export const CountUp: React.FC<{value: number; at: number; suffix?: string; decimals?: number; style?: CSSProperties}> = ({value, at, suffix = "", decimals = 0, style}) => {
  const frame = useCurrentFrame();
  const current = interpolate(frame, [at, at + 38], [0, value], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
  return <span style={style}>{current.toFixed(decimals)}{suffix}</span>;
};

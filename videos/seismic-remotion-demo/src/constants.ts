export const FPS = 30;

export const COLORS = {
  graphite: "#12100e",
  raised: "#1b1815",
  quiet: "#24201c",
  paper: "#f5efe6",
  muted: "#aaa097",
  border: "#39322c",
  orange: "#ff5a24",
  critical: "#e83f2d",
  warning: "#f3ad32",
  verified: "#8fa37b",
} as const;

export const SCENES = [
  {id: "blind-spot", frames: 300, audio: "01.wav", label: "THE BLIND SPOT"},
  {id: "graph-build", frames: 450, audio: "02.wav", label: "BUILD THE GRAPH"},
  {id: "blast-radius", frames: 630, audio: "03.wav", label: "EXACT BLAST RADIUS"},
  {id: "abstention", frames: 330, audio: "04.wav", label: "NO PATH, NO CLAIM"},
  {id: "mcp", frames: 600, audio: "05.wav", label: "STATELESS MCP"},
  {id: "native-graph", frames: 540, audio: "06.wav", label: "HYDRADB NATIVE"},
  {id: "proof", frames: 750, audio: "07.wav", label: "THE RECEIPTS"},
] as const;

export const SCENE_STARTS = SCENES.map((_, index) => SCENES.slice(0, index).reduce((sum, scene) => sum + scene.frames, 0));
export const TOTAL_FRAMES = SCENES.reduce((sum, scene) => sum + scene.frames, 0);

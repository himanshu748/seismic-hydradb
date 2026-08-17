import {Audio} from "@remotion/media";
import {AbsoluteFill, Sequence, staticFile} from "remotion";
import {SCENES, SCENE_STARTS} from "./constants";
import {BlindSpotScene} from "./scenes/BlindSpotScene";
import {GraphBuildScene} from "./scenes/GraphBuildScene";
import {BlastRadiusScene} from "./scenes/BlastRadiusScene";
import {AbstentionScene} from "./scenes/AbstentionScene";
import {McpScene} from "./scenes/McpScene";
import {NativeGraphScene} from "./scenes/NativeGraphScene";
import {ProofScene} from "./scenes/ProofScene";

const components = [BlindSpotScene, GraphBuildScene, BlastRadiusScene, AbstentionScene, McpScene, NativeGraphScene, ProofScene] as const;

export const SeismicLaunch: React.FC = () => (
  <AbsoluteFill style={{backgroundColor: "#12100e"}}>
    {SCENES.map((scene, index) => {
      const Component = components[index];
      return (
        <Sequence key={scene.id} from={SCENE_STARTS[index]} durationInFrames={scene.frames} premountFor={30}>
          <Component duration={scene.frames} />
          <Audio src={staticFile(`audio/${scene.audio}`)} volume={1} />
        </Sequence>
      );
    })}
  </AbsoluteFill>
);

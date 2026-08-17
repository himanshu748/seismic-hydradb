import {Composition, Folder} from "remotion";
import {SeismicLaunch} from "./SeismicLaunch";
import {FPS, SCENES, TOTAL_FRAMES} from "./constants";
import {BlindSpotScene} from "./scenes/BlindSpotScene";
import {GraphBuildScene} from "./scenes/GraphBuildScene";
import {BlastRadiusScene} from "./scenes/BlastRadiusScene";
import {AbstentionScene} from "./scenes/AbstentionScene";
import {McpScene} from "./scenes/McpScene";
import {NativeGraphScene} from "./scenes/NativeGraphScene";
import {ProofScene} from "./scenes/ProofScene";

const components = [
  BlindSpotScene,
  GraphBuildScene,
  BlastRadiusScene,
  AbstentionScene,
  McpScene,
  NativeGraphScene,
  ProofScene,
] as const;

export const Root: React.FC = () => (
  <>
    <Composition id="SeismicLaunch" component={SeismicLaunch} durationInFrames={TOTAL_FRAMES} fps={FPS} width={1920} height={1080} />
    <Folder name="Seismic-scenes">
      {SCENES.map((scene, index) => {
        const Component = components[index];
        return <Composition key={scene.id} id={`Seismic-${scene.id}`} component={Component} durationInFrames={scene.frames} fps={FPS} width={1920} height={1080} defaultProps={{duration: scene.frames}} />;
      })}
    </Folder>
  </>
);

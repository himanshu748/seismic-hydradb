import {mkdir, readFile, writeFile} from "node:fs/promises";
import {resolve} from "node:path";

const apiKey = process.env.MURF_API_KEY;
if (!apiKey) {
  throw new Error("MURF_API_KEY is required. Export it in the shell, never commit it.");
}

const voiceId = process.env.MURF_VOICE_ID ?? "en-US-terrell";
const selectedScenes = new Set(
  (process.env.MURF_SCENES ?? "1,2,3,4,5,6,7")
    .split(",")
    .map((value) => Number.parseInt(value.trim(), 10))
    .filter((value) => Number.isInteger(value) && value >= 1 && value <= 7),
);
const scriptPath = resolve("SCRIPT.md");
const outputDirectory = resolve("public/audio");
const script = await readFile(scriptPath, "utf8");
const scenes = script
  .split(/^# Scene \d+\s*$/gm)
  .map((section) => section.trim())
  .filter(Boolean);

if (scenes.length !== 7) {
  throw new Error(`Expected seven narration scenes in SCRIPT.md, found ${scenes.length}.`);
}

await mkdir(outputDirectory, {recursive: true});
let previousMetadata = [];
try {
  const current = JSON.parse(await readFile(resolve(outputDirectory, "murf-audio-meta.json"), "utf8"));
  previousMetadata = Array.isArray(current.scenes) ? current.scenes : [];
} catch {
  previousMetadata = [];
}
const metadata = previousMetadata.filter((item) => !selectedScenes.has(item.scene));

for (const [index, text] of scenes.entries()) {
  const sceneNumber = index + 1;
  if (!selectedScenes.has(sceneNumber)) {
    continue;
  }
  const response = await fetch("https://api.murf.ai/v1/speech/generate", {
    method: "POST",
    headers: {
      "api-key": apiKey,
      "content-type": "application/json",
    },
    body: JSON.stringify({
      text,
      voiceId,
      format: "WAV",
      sampleRate: 48000,
      channelType: "MONO",
      modelVersion: "GEN2",
      locale: "en-US",
      rate: 3,
      variation: 2,
      encodeAsBase64: true,
    }),
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Murf scene ${sceneNumber} failed with HTTP ${response.status}: ${detail}`);
  }

  const result = await response.json();
  if (!result.encodedAudio) {
    throw new Error(`Murf scene ${sceneNumber} returned no encoded audio.`);
  }

  const fileName = `${String(sceneNumber).padStart(2, "0")}.wav`;
  await writeFile(resolve(outputDirectory, fileName), Buffer.from(result.encodedAudio, "base64"));
  metadata.push({
    scene: sceneNumber,
    file: fileName,
    duration_seconds: result.audioLengthInSeconds,
    voice_id: voiceId,
  });
  process.stdout.write(`Generated scene ${sceneNumber}: ${result.audioLengthInSeconds}s\n`);
}

metadata.sort((left, right) => left.scene - right.scene);

await writeFile(
  resolve(outputDirectory, "murf-audio-meta.json"),
  `${JSON.stringify({generated_at: new Date().toISOString(), provider: "Murf GEN2", scenes: metadata}, null, 2)}\n`,
);

import {mkdir, readFile, writeFile} from "node:fs/promises";
import {resolve} from "node:path";

const apiKey = process.env.MURF_API_KEY;
if (!apiKey) {
  throw new Error("MURF_API_KEY is required. Export it in the shell, never commit it.");
}

const voiceId = process.env.MURF_VOICE_ID ?? "en-US-terrell";
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
const metadata = [];

for (const [index, text] of scenes.entries()) {
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
    throw new Error(`Murf scene ${index + 1} failed with HTTP ${response.status}: ${detail}`);
  }

  const result = await response.json();
  if (!result.encodedAudio) {
    throw new Error(`Murf scene ${index + 1} returned no encoded audio.`);
  }

  const fileName = `${String(index + 1).padStart(2, "0")}.wav`;
  await writeFile(resolve(outputDirectory, fileName), Buffer.from(result.encodedAudio, "base64"));
  metadata.push({
    scene: index + 1,
    file: fileName,
    duration_seconds: result.audioLengthInSeconds,
    voice_id: voiceId,
  });
  process.stdout.write(`Generated scene ${index + 1}: ${result.audioLengthInSeconds}s\n`);
}

await writeFile(
  resolve(outputDirectory, "murf-audio-meta.json"),
  `${JSON.stringify({generated_at: new Date().toISOString(), provider: "Murf GEN2", scenes: metadata}, null, 2)}\n`,
);

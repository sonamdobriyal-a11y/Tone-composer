import { useState } from "react";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import Textarea from "../components/ui/Textarea";
import Input from "../components/ui/Input";
import Slider from "../components/ui/Slider";
import { postBlob, postJSON } from "../lib/api";

type AbcResponse = { abc: string };

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export default function AITone() {
  const [mode, setMode] = useState<"fast" | "direct">("fast");
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [abc, setAbc] = useState<string | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);

  // Fast (ABC -> WAV)
  const [keySig, setKeySig] = useState("D");
  const [meter, setMeter] = useState("4/4");
  const [bars, setBars] = useState(16);

  // Direct audio controls
  const [bpm, setBpm] = useState(120);
  const [density, setDensity] = useState(0.8);
  const [brightness, setBrightness] = useState(0.7);
  const [guidance, setGuidance] = useState(4.0);
  const [duration, setDuration] = useState(12);

  async function runFast() {
    const res = await postJSON<AbcResponse>("/api/gemini/abc", {
      prompt,
      key: keySig,
      meter,
      unit_note_length: "1/8",
      bars,
    });
    setAbc(res.abc);
    const wav = await postBlob("/api/abc/audio/wav", { abc: res.abc });
    if (audioUrl) URL.revokeObjectURL(audioUrl);
    setAudioUrl(URL.createObjectURL(wav));
  }

  async function runDirect() {
    setAbc(null);
    const wav = await postBlob("/api/gemini/audio/wav", {
      prompt,
      bpm,
      density,
      brightness,
      guidance,
      duration_seconds: duration,
    });
    if (audioUrl) URL.revokeObjectURL(audioUrl);
    setAudioUrl(URL.createObjectURL(wav));
  }

  async function onGenerate() {
    setError(null);
    setLoading(true);
    try {
      if (mode === "fast") await runFast();
      else await runDirect();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Generation failed");
    } finally {
      setLoading(false);
    }
  }

  async function onDownload(kind: "wav" | "midi") {
    if (!abc) return;
    const blob = await postBlob(`/api/abc/audio/${kind}`, { abc });
    downloadBlob(blob, kind === "wav" ? "ai-tone.wav" : "ai-tone.mid");
  }

  return (
    <>
      <h1 className="title-font text-4xl font-semibold text-ink">AI Tone</h1>
      <Card className="p-8">
        <p className="text-muted leading-relaxed">
          Choose a fast path (generate ABC then synthesize locally) or direct audio synthesis. Keys
          and API credentials stay server-side.
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          <button
            onClick={() => setMode("fast")}
            className={[
              "rounded-full px-4 py-2 text-sm font-semibold border transition",
              mode === "fast"
                ? "bg-ink text-white border-ink"
                : "bg-white/70 text-ink border-black/10 hover:bg-black/5",
            ].join(" ")}
          >
            Fast (ABC -&gt; WAV)
          </button>
          <button
            onClick={() => setMode("direct")}
            className={[
              "rounded-full px-4 py-2 text-sm font-semibold border transition",
              mode === "direct"
                ? "bg-ink text-white border-ink"
                : "bg-white/70 text-ink border-black/10 hover:bg-black/5",
            ].join(" ")}
          >
            Direct audio
          </button>
        </div>
      </Card>

      <Card className="p-8">
        <label className="block text-sm font-medium text-ink">
          Prompt
          <div className="mt-2">
            <Textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              rows={6}
              placeholder="Cinematic raga mix with swelling Rhodes, tablas, and layered percussion..."
            />
          </div>
        </label>

        {mode === "fast" ? (
          <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-3">
            <label className="text-sm text-muted">
              Key
              <div className="mt-2">
                <Input value={keySig} onChange={(e) => setKeySig(e.target.value)} />
              </div>
            </label>
            <label className="text-sm text-muted">
              Meter
              <div className="mt-2">
                <Input value={meter} onChange={(e) => setMeter(e.target.value)} />
              </div>
            </label>
            <Slider label="Bars" min={4} max={32} step={4} value={bars} onChange={setBars} />
          </div>
        ) : (
          <div className="mt-6 grid grid-cols-1 gap-6 md:grid-cols-2">
            <Slider label="BPM" min={60} max={180} step={5} value={bpm} onChange={setBpm} />
            <Slider
              label="Duration (sec)"
              min={6}
              max={30}
              step={2}
              value={duration}
              onChange={setDuration}
            />
            <Slider
              label="Density"
              min={0.0}
              max={1.0}
              step={0.05}
              value={density}
              onChange={setDensity}
            />
            <Slider
              label="Brightness"
              min={0.0}
              max={1.0}
              step={0.05}
              value={brightness}
              onChange={setBrightness}
            />
            <Slider
              label="Guidance"
              min={0.5}
              max={12.0}
              step={0.5}
              value={guidance}
              onChange={setGuidance}
            />
          </div>
        )}

        <div className="mt-6 flex items-center gap-3">
          <Button onClick={onGenerate} disabled={loading}>
            {loading ? "Generating..." : "Generate"}
          </Button>
          {mode === "fast" && abc && (
            <>
              <Button variant="secondary" onClick={() => onDownload("midi")}>
                Download MIDI
              </Button>
              <Button variant="secondary" onClick={() => onDownload("wav")}>
                Download WAV
              </Button>
            </>
          )}
        </div>
        {error && <div className="mt-4 text-sm text-red-700">{error}</div>}
      </Card>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <Card className="p-8">
          <h2 className="title-font text-xl font-semibold">Preview</h2>
          <div className="mt-4">
            {audioUrl ? (
              <audio controls src={audioUrl} className="w-full" />
            ) : (
              <div className="text-sm text-muted">Generate to preview audio.</div>
            )}
          </div>
        </Card>

        <Card className="p-8">
          <h2 className="title-font text-xl font-semibold">ABC (Fast mode)</h2>
          <div className="mt-4">
            {abc ? (
              <pre className="max-h-[360px] overflow-auto rounded-2xl bg-black/90 p-4 text-xs text-white">
                {abc}
              </pre>
            ) : (
              <div className="text-sm text-muted">ABC will appear here when using Fast mode.</div>
            )}
          </div>
        </Card>
      </div>
    </>
  );
}


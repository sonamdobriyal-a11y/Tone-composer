import { useMemo, useState } from "react";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import Textarea from "../components/ui/Textarea";
import Slider from "../components/ui/Slider";
import { postBlob, postJSON } from "../lib/api";

type HFAbcResponse = { abc: string };

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

export default function Chatbot() {
  const [prompt, setPrompt] = useState("");
  const [topP, setTopP] = useState(0.9);
  const [temperature, setTemperature] = useState(1.0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [abc, setAbc] = useState<string | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);

  const examples = useMemo(
    () => [
      {
        title: "North Indian raga meditation",
        details: "Raga – Yaman · Meter – 6/8 · Key – D · Tempo – Medium · Style – Calm, flowing",
      },
      {
        title: "Rhodes-laced Bhairavi stroll",
        details:
          "Folk-inspired raga Bhairavi with lush Rhodes chords and vibraphone accents over a walking bass.",
      },
    ],
    []
  );

  async function onGenerate() {
    setError(null);
    setLoading(true);
    try {
      const res = await postJSON<HFAbcResponse>("/api/hf/abc", {
        prompt,
        top_p: topP,
        temperature,
        max_length: 1024,
      });
      setAbc(res.abc);

      const wav = await postBlob("/api/abc/audio/wav", { abc: res.abc });
      if (audioUrl) URL.revokeObjectURL(audioUrl);
      setAudioUrl(URL.createObjectURL(wav));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Generation failed");
    } finally {
      setLoading(false);
    }
  }

  async function onDownload(kind: "wav" | "midi") {
    if (!abc) return;
    const blob = await postBlob(`/api/abc/audio/${kind}`, { abc });
    downloadBlob(blob, kind === "wav" ? "fusion.wav" : "fusion.mid");
  }

  return (
    <>
      <h1 className="title-font text-4xl font-semibold text-ink">Tone Generation</h1>
      <Card className="p-8">
        <p className="text-muted leading-relaxed">
          Provide a prompt describing mood, instrumentation, or stylistic focus and generate a short
          fusion-inspired stanza of ABC notation.
          <br />
          Use the controls below to tune randomness and shape the fusion feel before downloading
          MIDI/WAV.
        </p>
      </Card>

      <Card className="p-8">
        <label className="block text-sm font-medium text-ink">
          Prompt
          <div className="mt-2">
            <Textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              rows={6}
              placeholder="Gently sway between raga Bhairavi and 7th-chord jazz vocab..."
            />
          </div>
        </label>

        <div className="mt-6 grid grid-cols-1 gap-6 md:grid-cols-2">
          <Slider label="Top-p" min={0.3} max={1.0} step={0.05} value={topP} onChange={setTopP} />
          <Slider
            label="Temperature"
            min={0.2}
            max={2.0}
            step={0.1}
            value={temperature}
            onChange={setTemperature}
          />
        </div>

        <div className="mt-6 flex items-center gap-3">
          <Button onClick={onGenerate} disabled={loading}>
            {loading ? "Generating..." : "Generate"}
          </Button>
          {abc && (
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
          <h2 className="title-font text-xl font-semibold">Prompt Examples</h2>
          <div className="mt-4 space-y-4">
            {examples.map((e) => (
              <div key={e.title} className="rounded-2xl bg-white/60 p-4 border border-black/5">
                <div className="font-semibold text-ink">{e.title}</div>
                <div className="mt-1 text-sm text-muted">{e.details}</div>
              </div>
            ))}
          </div>
        </Card>

        <Card className="p-8">
          <h2 className="title-font text-xl font-semibold">Output</h2>
          <div className="mt-4">
            {audioUrl ? (
              <audio controls src={audioUrl} className="w-full" />
            ) : (
              <div className="text-sm text-muted">Generate to preview audio.</div>
            )}
          </div>
          <div className="mt-4">
            {abc ? (
              <pre className="max-h-[360px] overflow-auto rounded-2xl bg-black/90 p-4 text-xs text-white">
                {abc}
              </pre>
            ) : (
              <div className="text-sm text-muted">ABC notation will appear here.</div>
            )}
          </div>
        </Card>
      </div>
    </>
  );
}


import Card from "../components/ui/Card";

export default function Home() {
  return (
    <>
      <h1 className="title-font text-4xl font-semibold text-ink">Indian x Jazz Fusion</h1>
      <Card className="p-8">
        <h2 className="title-font text-2xl font-semibold">Introduction</h2>
        <p className="mt-3 text-muted leading-relaxed">
          This platform explores the creative intersection between Indian classical ragas and
          jazz harmony/improvisation. Generate ABC notation and audition a quick synthesized
          sketch, then export MIDI/WAV for further production.
        </p>
      </Card>
      <Card className="p-8">
        <h2 className="title-font text-2xl font-semibold">Objectives</h2>
        <ul className="mt-3 list-disc pl-6 text-muted space-y-1">
          <li>Explore raga tonal structures</li>
          <li>Blend with jazz harmony and rhythmic feel</li>
          <li>Iterate prompts to shape motifs</li>
          <li>Export ideas to DAW via MIDI</li>
        </ul>
      </Card>
    </>
  );
}


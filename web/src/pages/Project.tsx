import Card from "../components/ui/Card";

export default function Project() {
  return (
    <>
      <h1 className="title-font text-4xl font-semibold text-ink">Fusion Concept</h1>
      <Card className="p-8">
        <h2 className="title-font text-2xl font-semibold">Why Raga and Jazz?</h2>
        <p className="mt-3 text-muted leading-relaxed">
          Indian classical music and jazz share improvisation, modal exploration, and emotional
          expression. Ragascapes provide melodic constraints; jazz adds harmonic color and rhythmic
          flexibility.
        </p>
      </Card>
      <Card className="p-8">
        <h2 className="title-font text-2xl font-semibold">Fusion Approach</h2>
        <p className="mt-3 text-muted leading-relaxed">
          Map raga phrases to compatible jazz modes, preserve raga identity while introducing chord
          voicings, and iterate motifs through prompt-driven generation.
        </p>
      </Card>
    </>
  );
}


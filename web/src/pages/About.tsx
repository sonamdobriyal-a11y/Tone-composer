import Card from "../components/ui/Card";

export default function About() {
  return (
    <>
      <h1 className="title-font text-4xl font-semibold text-ink">About</h1>
      <Card className="p-8">
        <p className="text-muted leading-relaxed">
          This project explores a music-technology workflow for fusing Indian classical ragas and
          jazz vocabulary. The app focuses on fast iteration: prompt, generate, audition, and export.
        </p>
      </Card>
    </>
  );
}


import Card from "../components/ui/Card";

export default function Contact() {
  return (
    <>
      <h1 className="title-font text-4xl font-semibold text-ink">Contact</h1>
      <Card className="p-8">
        <p className="text-muted">For questions or collaboration, reach out:</p>
        <div className="mt-4 rounded-2xl bg-white/60 p-4 border border-black/5">
          <div className="text-sm font-semibold text-ink">Email</div>
          <div className="mt-1 text-sm text-muted">vihaankulkarni28@gmail.com</div>
        </div>
      </Card>
    </>
  );
}


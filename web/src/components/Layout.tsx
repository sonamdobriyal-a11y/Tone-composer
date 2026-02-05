import { NavLink } from "react-router-dom";

const links = [
  { to: "/", label: "Home" },
  { to: "/project", label: "Project" },
  { to: "/chatbot", label: "Chatbot" },
  { to: "/ai-tone", label: "AI Tone" },
  { to: "/about", label: "About" },
  { to: "/contact", label: "Contact" }
];

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen">
      <div className="mx-auto max-w-[1200px] px-6 py-6">
        <div className="grid grid-cols-1 gap-6 md:grid-cols-[260px_1fr]">
          <aside className="glass rounded-card shadow-card border border-black/5 p-5">
            <div className="title-font text-lg font-semibold text-ink">Vihaan</div>
            <div className="mt-1 text-sm text-muted">
              Raga x Jazz generation studio
            </div>
            <nav className="mt-6 space-y-2">
              {links.map((l) => (
                <NavLink
                  key={l.to}
                  to={l.to}
                  className={({ isActive }) =>
                    [
                      "block rounded-xl px-3 py-2 text-sm font-medium transition",
                      isActive
                        ? "bg-ink text-white"
                        : "text-ink hover:bg-black/5"
                    ].join(" ")
                  }
                >
                  {l.label}
                </NavLink>
              ))}
            </nav>
            <div className="mt-8 rounded-2xl bg-white/60 p-4 text-xs text-muted">
              Tip: Keep prompts short and specific (mood + instruments + meter).
            </div>
          </aside>

          <main className="space-y-6">{children}</main>
        </div>
      </div>
    </div>
  );
}


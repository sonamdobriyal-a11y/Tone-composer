import React from "react";

export default function Textarea({
  className = "",
  ...props
}: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      className={`w-full rounded-2xl border border-black/10 bg-white/80 px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-accent/60 ${className}`}
      {...props}
    />
  );
}


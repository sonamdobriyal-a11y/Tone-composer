import React from "react";

export default function Input({
  className = "",
  ...props
}: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={`w-full rounded-xl border border-black/10 bg-white/80 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-accent/60 ${className}`}
      {...props}
    />
  );
}


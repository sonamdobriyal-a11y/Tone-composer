import React from "react";

type Props = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary";
};

export default function Button({ variant = "primary", className = "", ...props }: Props) {
  const base =
    "inline-flex items-center justify-center rounded-full px-5 py-2 text-sm font-semibold transition shadow-sm";
  const styles =
    variant === "primary"
      ? "bg-ink text-white hover:opacity-90"
      : "bg-white text-ink border border-black/10 hover:bg-black/5";
  return <button className={`${base} ${styles} ${className}`} {...props} />;
}


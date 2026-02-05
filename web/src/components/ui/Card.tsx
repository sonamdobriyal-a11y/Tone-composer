import React from "react";

export default function Card({
  className = "",
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={`glass rounded-card shadow-card border border-black/5 ${className}`}
      {...props}
    />
  );
}


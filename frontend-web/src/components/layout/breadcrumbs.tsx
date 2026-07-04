"use client";

import { usePathname } from "next/navigation";

export function Breadcrumbs() {
  const pathname = usePathname();
  const segments = pathname.split("/").filter(Boolean);

  return (
    <nav className="flex items-center gap-1.5 text-sm text-muted-foreground">
      {segments.map((segment, i) => (
        <span key={i} className="flex items-center gap-1.5">
          {i > 0 && <span>/</span>}
          <span
            className={
              i === segments.length - 1 ? "text-foreground font-medium" : ""
            }
          >
            {segment.charAt(0).toUpperCase() + segment.slice(1)}
          </span>
        </span>
      ))}
    </nav>
  );
}

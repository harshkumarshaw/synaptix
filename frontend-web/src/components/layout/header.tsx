"use client";

import { SidebarTrigger } from "@/components/ui/sidebar";
import { Separator } from "@/components/ui/separator";
import { Breadcrumbs } from "./breadcrumbs";

export function Header() {
  return (
    <header className="flex h-14 items-center gap-4 border-b bg-background px-6">
      <SidebarTrigger />
      <Separator orientation="vertical" className="h-6" />
      <Breadcrumbs />
    </header>
  );
}

# 03-frontend — Learning Memory

Accumulated learnings, patterns, and discoveries.

## Patterns Established

- **Tailwind CSS v3 + shadcn Variables Mapping**: Since the workspace is set up on Tailwind CSS v3, and the newer shadcn CLI generates classes expecting CSS variables configuration, you should map custom CSS variables using the `hsl(var(--...))` utility under `extend.colors` inside `tailwind.config.ts`.
- **Developer Auth Bypass**: To test layout shells, navigation menus, and protected routing locally without spawning all backend FastAPI services, add a developer bypass buttons container inside `login-form.tsx` that triggers Zustand's state setter with mock base64-encoded JWT tokens containing role properties.

## Anti-patterns Discovered

- **Using asChild on Base UI Buttons**: Do not use `asChild` on newer shadcn button/sidebar primitives that utilize `@base-ui/react`. Use the `render={<Link ... />}` prop instead, or it will throw TS compilation errors.

## Useful Code Snippets

```typescript
// Custom render prop structure for SidebarMenuButton
<SidebarMenuButton
  isActive={pathname === item.href}
  render={
    <Link href={item.href} className="flex items-center gap-3">
      <item.icon className="h-4 w-4" />
      <span>{item.label}</span>
    </Link>
  }
/>
```

## Cross-Agent Insights

- None.

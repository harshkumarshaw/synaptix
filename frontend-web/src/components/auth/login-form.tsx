"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuthStore } from "@/stores/auth-store";
import { useRouter } from "next/navigation";

const loginSchema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z.string().min(1, "Password is required"),
});

type LoginValues = z.infer<typeof loginSchema>;

interface LoginFormProps {
  onSubmit: (email: string, password: string) => Promise<void>;
  error: string | null;
  loading: boolean;
}

// Pre-generated mock JWTs for local development bypass
const MOCK_TOKENS = {
  admin:
    "eyJhbGciOiJub25lIn0.eyJzdWIiOiJkZWQtYWRtaW4tMTIzIiwidGVuYW50X2lkIjoiZGVkLXRlbmFudC00NTYiLCJlbWFpbCI6ImFkbWluQGptbi5lZHUuaW4iLCJuYW1lIjoiRGV2IEFkbWluIiwicm9sZSI6ImFkbWluIn0.",
  faculty:
    "eyJhbGciOiJub25lIn0.eyJzdWIiOiJkZWQtZmFjdWx0eS0xMjMiLCJ0ZW5hbnRfaWQiOiJkZWQtdGVuYW50LTQ1NiIsImVtYWlsIjoiZmFjdWx0eUBqbW4uZWR1LmluIiwibmFtZSI6IkRldiBGYWN1bHR5Iiwicm9sZSI6ImZhY3VsdHkifQ.",
  student:
    "eyJhbGciOiJub25lIn0.eyJzdWIiOiJkZWQtc3R1ZGVudC0xMjMiLCJ0ZW5hbnRfaWQiOiJkZWQtdGVuYW50LTQ1NiIsImVtYWlsIjoic3R1ZGVudEBqbW4uZWR1LmluIiwibmFtZSI6IkRldiBTdHVkZW50Iiwicm9sZSI6InN0dWRlbnQiLCJzdHVkZW50X2lkIjoic3RkLTc4OSJ9.",
};

export function LoginForm({ onSubmit, error, loading }: LoginFormProps) {
  const router = useRouter();
  const form = useForm<LoginValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  });

  async function handleSubmit(values: LoginValues) {
    await onSubmit(values.email, values.password);
  }

  function handleDevBypass(role: "admin" | "faculty" | "student") {
    const token = MOCK_TOKENS[role];
    useAuthStore.getState().setAuth(token);
    router.push("/dashboard");
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="text-center text-xl">Sign in</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              placeholder="faculty@jmn.edu.in"
              {...form.register("email")}
            />
            {form.formState.errors.email && (
              <p className="text-sm text-destructive">
                {form.formState.errors.email.message}
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              placeholder="••••••••"
              {...form.register("password")}
            />
            {form.formState.errors.password && (
              <p className="text-sm text-destructive">
                {form.formState.errors.password.message}
              </p>
            )}
          </div>

          {error && (
            <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
              {error}
            </div>
          )}

          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? "Signing in..." : "Sign in"}
          </Button>
        </form>

        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <span className="w-full border-t" />
          </div>
          <div className="relative flex justify-center text-xs uppercase">
            <span className="bg-card px-2 text-muted-foreground">
              Developer Bypass
            </span>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleDevBypass("admin")}
          >
            Admin
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleDevBypass("faculty")}
          >
            Faculty
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleDevBypass("student")}
          >
            Student
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

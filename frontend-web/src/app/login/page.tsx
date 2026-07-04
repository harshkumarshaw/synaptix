"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { login } from "@/lib/auth";
import { LoginForm } from "@/components/auth/login-form";

export default function LoginPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleLogin(email: string, password: string) {
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
      router.push("/dashboard");
    } catch (err) {
      const errorMsg =
        (err as { response?: { data?: { detail?: { message?: string } } } })
          .response?.data?.detail?.message || "Login failed";
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 dark:bg-zinc-950">
      <div className="w-full max-w-md space-y-8 px-4">
        {/* Logo / Branding */}
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold tracking-tight">Synaptix</h1>
          <p className="text-sm text-muted-foreground">
            Academic Operations & Intelligence Platform
          </p>
        </div>

        {/* Login Form */}
        <LoginForm onSubmit={handleLogin} error={error} loading={loading} />

        {/* Footer */}
        <p className="text-center text-xs text-muted-foreground">
          JMN Medical College &middot; NMC CBME Compliant
        </p>
      </div>
    </div>
  );
}

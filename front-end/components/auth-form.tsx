"use client";

import { environment } from "@/lib/env";
import { useRouter } from "next/navigation";
import type { SubmitEvent } from "react";
import { useEffect, useState } from "react";

function errorMessage(body: string, fallback: string): string {
  try {
    const parsed = JSON.parse(body) as { detail?: string | Array<{ msg?: string }> };
    if (typeof parsed.detail === "string") return parsed.detail;
    if (Array.isArray(parsed.detail)) return parsed.detail[0]?.msg ?? fallback;
    return fallback;
  } catch {
    return body || fallback;
  }
}

export function AuthForm() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    async function restoreSession() {
      try {
        const response = await fetch(`${environment.API_BASE_URL}/api/v1/auth/me`, {
          credentials: "include",
          cache: "no-store",
        });
        if (response.ok) router.replace("/workspace");
      } catch {
        // FastAPI may still be starting; the form remains usable.
      }
    }

    void restoreSession();
  }, [router]);

  async function submit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError("");

    const payload = mode === "signup" ? { name, email, password } : { email, password };

    try {
      const response = await fetch(
        `${environment.API_BASE_URL}/api/v1/auth/${mode}`,
        {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        },
      );
      const body = await response.text();
      if (!response.ok) {
        throw new Error(errorMessage(body, mode === "signup" ? "Signup failed." : "Login failed."));
      }

      router.push("/workspace");
      router.refresh();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Could not reach the API.");
    } finally {
      setSubmitting(false);
    }
  }

  function changeMode(nextMode: "login" | "signup") {
    setMode(nextMode);
    setError("");
    setPassword("");
  }

  return (
    <main className="login-shell">
      <section className="login-card">
        <div className="brand-mark" aria-hidden="true">IH</div>
        <p className="eyebrow">AI inference platform</p>
        <h1>{mode === "login" ? "Welcome back." : "Create your account."}</h1>
        <p className="login-copy">
          Sign in to choose a use case, select a model, and run inference.
        </p>

        <div className="auth-tabs" aria-label="Authentication mode">
          <button
            className={mode === "login" ? "active" : ""}
            onClick={() => changeMode("login")}
            type="button"
          >
            Log in
          </button>
          <button
            className={mode === "signup" ? "active" : ""}
            onClick={() => changeMode("signup")}
            type="button"
          >
            Sign up
          </button>
        </div>

        <form className="auth-form" onSubmit={submit}>
          {mode === "signup" && (
            <label>
              Name
              <input
                autoComplete="name"
                maxLength={120}
                onChange={(event) => setName(event.target.value)}
                required
                type="text"
                value={name}
              />
            </label>
          )}
          <label>
            Email
            <input
              autoComplete="email"
              maxLength={320}
              onChange={(event) => setEmail(event.target.value)}
              required
              type="email"
              value={email}
            />
          </label>
          <label>
            Password
            <input
              autoComplete={mode === "login" ? "current-password" : "new-password"}
              maxLength={128}
              minLength={mode === "signup" ? 8 : 1}
              onChange={(event) => setPassword(event.target.value)}
              required
              type="password"
              value={password}
            />
          </label>

          {error && <p className="field-error auth-error">{error}</p>}

          <button className="primary-button login-button" disabled={submitting} type="submit">
            {submitting ? "Please wait…" : mode === "login" ? "Log in" : "Create account"}
          </button>
        </form>
      </section>
    </main>
  );
}

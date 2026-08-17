"use client";

import { environment } from "@/lib/env";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

type CurrentUser = {
  id: number;
  email: string;
  name: string;
  role: "user" | "tester";
};

type UseCase = {
  id: number;
  name: string;
  description: string | null;
  is_ready: boolean;
};

type RegisteredModel = {
  id: number;
  use_case_id: number;
  name: string;
  version: string;
  is_active: boolean;
};

const DEFAULT_INPUT = JSON.stringify(
  { prompt: "Enter the input expected by this model" },
  null,
  2,
);

function errorMessage(body: string, fallback: string): string {
  try {
    const parsed = JSON.parse(body) as { detail?: string };
    return parsed.detail ?? fallback;
  } catch {
    return body || fallback;
  }
}

export function Workspace() {
  const router = useRouter();
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [useCases, setUseCases] = useState<UseCase[]>([]);
  const [models, setModels] = useState<RegisteredModel[]>([]);
  const [selectedUseCase, setSelectedUseCase] = useState<number | null>(null);
  const [selectedModel, setSelectedModel] = useState<number | null>(null);
  const [input, setInput] = useState(DEFAULT_INPUT);
  const [output, setOutput] = useState("");
  const [catalogError, setCatalogError] = useState("");
  const [invokeError, setInvokeError] = useState("");
  const [loadingUseCases, setLoadingUseCases] = useState(true);
  const [loadingModels, setLoadingModels] = useState(false);
  const [invoking, setInvoking] = useState(false);

  const apiFetch = useCallback(
    async (path: string, init?: RequestInit) => {
      const headers = new Headers(init?.headers);
      if (init?.body) headers.set("Content-Type", "application/json");

      const response = await fetch(`${environment.API_BASE_URL}${path}`, {
        ...init,
        cache: "no-store",
        credentials: "include",
        headers,
      });
      if (response.status === 401) router.replace("/");
      return response;
    },
    [router],
  );

  useEffect(() => {
    let cancelled = false;

    async function loadWorkspace() {
      setLoadingUseCases(true);
      setCatalogError("");
      try {
        const userResponse = await apiFetch("/api/v1/auth/me");
        const userBody = await userResponse.text();
        if (!userResponse.ok) {
          if (userResponse.status === 401) return;
          throw new Error(errorMessage(userBody, "Could not load your account."));
        }
        if (!cancelled) setUser(JSON.parse(userBody) as CurrentUser);

        const response = await apiFetch("/api/v1/use-cases");
        const body = await response.text();
        if (!response.ok) throw new Error(errorMessage(body, "Could not load use cases."));
        if (!cancelled) setUseCases(JSON.parse(body) as UseCase[]);
      } catch (error) {
        if (!cancelled) {
          setCatalogError(error instanceof Error ? error.message : "Could not load use cases.");
        }
      } finally {
        if (!cancelled) setLoadingUseCases(false);
      }
    }

    void loadWorkspace();
    return () => {
      cancelled = true;
    };
  }, [apiFetch]);

  async function logout() {
    try {
      await apiFetch("/api/v1/auth/logout", { method: "POST" });
    } finally {
      router.replace("/");
      router.refresh();
    }
  }

  async function chooseUseCase(useCaseId: number) {
    setSelectedUseCase(useCaseId);
    setSelectedModel(null);
    setModels([]);
    setOutput("");
    setInvokeError("");
    setCatalogError("");
    setLoadingModels(true);

    try {
      const response = await apiFetch(`/api/v1/use-cases/${useCaseId}/models`);
      const body = await response.text();
      if (!response.ok) throw new Error(errorMessage(body, "Could not load models."));
      setModels(JSON.parse(body) as RegisteredModel[]);
    } catch (error) {
      setCatalogError(error instanceof Error ? error.message : "Could not load models.");
    } finally {
      setLoadingModels(false);
    }
  }

  async function invokeModel() {
    if (selectedModel === null) return;

    let parsedInput: Record<string, unknown>;
    try {
      const parsed: unknown = JSON.parse(input);
      if (parsed === null || Array.isArray(parsed) || typeof parsed !== "object") {
        throw new Error("Input must be a JSON object.");
      }
      parsedInput = parsed as Record<string, unknown>;
      if (Object.keys(parsedInput).length === 0) throw new Error("Input cannot be empty.");
    } catch (error) {
      setInvokeError(error instanceof Error ? error.message : "Input is not valid JSON.");
      return;
    }

    setInvoking(true);
    setInvokeError("");
    setOutput("");

    try {
      const response = await apiFetch(`/api/v1/models/${selectedModel}/invoke`, {
        method: "POST",
        body: JSON.stringify({ input: parsedInput }),
      });

      if (!response.ok) {
        const body = await response.text();
        throw new Error(errorMessage(body, `Request failed with status ${response.status}.`));
      }
      if (!response.body) {
        setOutput("The model returned an empty response.");
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let completeOutput = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        completeOutput += decoder.decode(value, { stream: true });
        setOutput(completeOutput);
      }
      completeOutput += decoder.decode();
      setOutput(completeOutput || "The model returned an empty response.");
    } catch (error) {
      setInvokeError(error instanceof Error ? error.message : "The model request failed.");
    } finally {
      setInvoking(false);
    }
  }

  const activeUseCase = useCases.find((item) => item.id === selectedUseCase);
  const activeModel = models.find((item) => item.id === selectedModel);

  return (
    <main className="workspace-shell">
      <header className="topbar">
        <a className="brand" href="/workspace">
          <span className="brand-mark small" aria-hidden="true">IH</span>
          <span>Inference Hub</span>
        </a>
        <div className="account">
          <div className="account-text">
            <span className="account-name">{user?.name ?? "Account"}</span>
            {user && <span className="account-role">{user.role}</span>}
          </div>
          <button className="logout-button" onClick={() => void logout()} type="button">
            Log out
          </button>
        </div>
      </header>

      <div className="workspace-content">
        <section className="page-heading">
          <p className="eyebrow">Model catalog</p>
          <h1>Choose what you want to run.</h1>
          <p>Select a use case and one of its available models, then provide the request input.</p>
        </section>

        {catalogError && <div className="error-banner">{catalogError}</div>}

        <section className="catalog-section" aria-labelledby="use-cases-title">
          <div className="section-title">
            <span className="step-number">1</span>
            <div>
              <h2 id="use-cases-title">Use case</h2>
              <p>What are you trying to do?</p>
            </div>
          </div>

          {loadingUseCases ? (
            <p className="muted-state">Loading use cases…</p>
          ) : useCases.length === 0 ? (
            <p className="muted-state">No use cases are currently available.</p>
          ) : (
            <div className="choice-grid">
              {useCases.map((useCase) => (
                <button
                  className={`choice-card ${selectedUseCase === useCase.id ? "selected" : ""}`}
                  key={useCase.id}
                  onClick={() => void chooseUseCase(useCase.id)}
                  type="button"
                >
                  <span className="choice-name">{useCase.name}</span>
                  <span className="choice-description">
                    {useCase.description ?? "No description provided."}
                  </span>
                  {!useCase.is_ready && <span className="status-badge testing">Testing</span>}
                </button>
              ))}
            </div>
          )}
        </section>

        {selectedUseCase !== null && (
          <section className="catalog-section" aria-labelledby="models-title">
            <div className="section-title">
              <span className="step-number">2</span>
              <div>
                <h2 id="models-title">Model</h2>
                <p>Available for {activeUseCase?.name ?? "this use case"}.</p>
              </div>
            </div>

            {loadingModels ? (
              <p className="muted-state">Loading models…</p>
            ) : models.length === 0 ? (
              <p className="muted-state">No models are currently available.</p>
            ) : (
              <div className="choice-grid models-grid">
                {models.map((model) => (
                  <button
                    className={`choice-card model-card ${selectedModel === model.id ? "selected" : ""}`}
                    key={model.id}
                    onClick={() => {
                      setSelectedModel(model.id);
                      setOutput("");
                      setInvokeError("");
                    }}
                    type="button"
                  >
                    <span className="model-heading">
                      <span className="choice-name">{model.name}</span>
                      <span className={`status-dot ${model.is_active ? "active" : "inactive"}`}>
                        {model.is_active ? "Active" : "Testing"}
                      </span>
                    </span>
                    <span className="choice-description">Version {model.version}</span>
                  </button>
                ))}
              </div>
            )}
          </section>
        )}

        {selectedModel !== null && (
          <section className="catalog-section" aria-labelledby="invoke-title">
            <div className="section-title">
              <span className="step-number">3</span>
              <div>
                <h2 id="invoke-title">Run inference</h2>
                <p>Send a JSON object to {activeModel?.name ?? "the selected model"}.</p>
              </div>
            </div>

            <div className="inference-grid">
              <div className="editor-panel">
                <label htmlFor="model-input">Request input</label>
                <textarea
                  id="model-input"
                  onChange={(event) => setInput(event.target.value)}
                  spellCheck={false}
                  value={input}
                />
                {invokeError && <p className="field-error">{invokeError}</p>}
                <button
                  className="primary-button"
                  disabled={invoking}
                  onClick={() => void invokeModel()}
                  type="button"
                >
                  {invoking ? "Running…" : "Run model"}
                </button>
              </div>

              <div className="editor-panel output-panel">
                <div className="output-heading">
                  <span>Response</span>
                  {invoking && <span className="streaming-label">Streaming</span>}
                </div>
                <pre className={output ? "" : "empty-output"}>
                  {output || "The model response will appear here."}
                </pre>
              </div>
            </div>
          </section>
        )}
      </div>
    </main>
  );
}

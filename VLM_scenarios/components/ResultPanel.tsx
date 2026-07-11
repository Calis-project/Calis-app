"use client";

import { AlertCircle, CheckCircle2, Loader2 } from "lucide-react";

import type { AnalyzeResponse } from "@/lib/types/analysis";

type ResultPanelProps = {
  busy: boolean;
  error?: string;
  result?: AnalyzeResponse;
};

export function ResultPanel({ busy, error, result }: ResultPanelProps) {
  return (
    <section className="result-panel" aria-live="polite">
      <div className="section-heading">
        <span>Coach response</span>
        {busy ? (
          <span className="state-pill">
            <Loader2 aria-hidden="true" className="spin" size={15} />
            Running
          </span>
        ) : null}
        {!busy && result?.ok ? (
          <span className="state-pill success">
            <CheckCircle2 aria-hidden="true" size={15} />
            {result.timingMs} ms
            {result.usage ? ` · ${result.usage.totalTokens} tok` : ""}
            {result.estCostUsd !== undefined
              ? ` · ~$${result.estCostUsd.toFixed(4)}`
              : ""}
          </span>
        ) : null}
      </div>

      {error ? (
        <div className="error-box">
          <AlertCircle aria-hidden="true" size={18} />
          <span>{error}</span>
        </div>
      ) : null}

      {!error && result?.ok ? (
        <div className="response-text">{result.text}</div>
      ) : null}

      {!busy && !error && !result ? (
        <div className="empty-result">
          No coach response yet — analysis output appears here.
        </div>
      ) : null}
    </section>
  );
}

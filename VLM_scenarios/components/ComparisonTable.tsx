"use client";

import type { AnalyzeSuccess } from "@/lib/types/analysis";

export type HistoryRow = AnalyzeSuccess & { label: string };

type ComparisonTableProps = {
  rows: HistoryRow[];
};

export function ComparisonTable({ rows }: ComparisonTableProps) {
  return (
    <section className="comparison-panel">
      <div className="section-heading">
        <span>Run history</span>
        <small>{rows.length} runs</small>
      </div>

      {rows.length ? (
        <div className="comparison-list">
          {rows.map((row, index) => (
            <div className="comparison-row" key={`${row.label}-${row.timingMs}-${index}`}>
              <span>{row.label}</span>
              <span>{row.model}</span>
              <span>{row.usage ? `${row.usage.totalTokens} tok` : "–"}</span>
              <span>
                {row.estCostUsd !== undefined ? `~$${row.estCostUsd.toFixed(4)}` : "–"}
              </span>
              <strong>{row.timingMs} ms</strong>
            </div>
          ))}
        </div>
      ) : (
        <div className="empty-strip">No completed runs</div>
      )}
    </section>
  );
}

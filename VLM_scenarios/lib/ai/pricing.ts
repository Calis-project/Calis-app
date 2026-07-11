import type { TokenUsage } from "@/lib/types/analysis";

// Approximate Gemini PAID-tier pricing, USD per 1M tokens.
// ⚠️ VERIFY & EDIT — Google changes prices often. These are best-effort
// defaults used only to show a rough "what this would cost on paid" figure;
// the free tier bills nothing. Ordered specific → general (first match wins).
type Price = { inputPerM: number; outputPerM: number };

const PRICES: { match: RegExp; price: Price }[] = [
  { match: /flash-lite/i, price: { inputPerM: 0.1, outputPerM: 0.4 } },
  { match: /flash/i, price: { inputPerM: 0.3, outputPerM: 2.5 } },
  { match: /pro/i, price: { inputPerM: 1.25, outputPerM: 10.0 } },
];

const FALLBACK: Price = { inputPerM: 0.3, outputPerM: 2.5 };

export function priceForModel(model: string): Price {
  return PRICES.find((entry) => entry.match.test(model))?.price ?? FALLBACK;
}

// Rough USD cost for one call, or undefined when token usage is unavailable.
export function estimateCostUsd(
  model: string,
  usage?: TokenUsage,
): number | undefined {
  if (!usage) {
    return undefined;
  }
  const { inputPerM, outputPerM } = priceForModel(model);
  // Gemini bills "thinking" tokens as output but reports them separately from
  // candidatesTokenCount. total - prompt recovers the full billable output
  // (visible reply + hidden reasoning); fall back to outputTokens if total is 0.
  const billableOutput = Math.max(
    usage.outputTokens,
    usage.totalTokens - usage.promptTokens,
  );
  const cost =
    (usage.promptTokens / 1_000_000) * inputPerM +
    (billableOutput / 1_000_000) * outputPerM;
  return Math.round(cost * 1_000_000) / 1_000_000; // 6 dp
}

import "server-only";

// Rolling alias that always points at the current Gemini Flash model — avoids
// pinning a version string that 404s when Google rotates model IDs. Override
// with GEMINI_MODEL (e.g. "gemini-flash-lite-latest" for a cheaper/faster path).
const DEFAULT_MODEL = "gemini-flash-latest";
const PLACEHOLDER_KEY = "PASTE_YOUR_GEMINI_API_KEY_HERE";

export function getGeminiModel() {
  return process.env.GEMINI_MODEL || DEFAULT_MODEL;
}

export function getGeminiApiKey() {
  return process.env.GEMINI_API_KEY || process.env.GOOGLE_API_KEY || "";
}

export function hasGeminiApiKey() {
  const key = getGeminiApiKey();
  return Boolean(key && key !== PLACEHOLDER_KEY);
}

const http = require("http");
const fs = require("fs");
const path = require("path");

loadLocalEnv();

const PORT = Number(process.env.PORT || 3000);
const GEMINI_API_KEY = process.env.GEMINI_API_KEY || process.env.GOOGLE_API_KEY || "";
const GEMINI_KEY_PLACEHOLDER = "PASTE_YOUR_GEMINI_API_KEY_HERE";
const GEMINI_MODEL = process.env.GEMINI_MODEL || "gemini-3.5-flash";
const MAX_BODY_BYTES = 20 * 1024 * 1024;

function loadLocalEnv() {
  const envPath = path.join(__dirname, ".env");

  if (!fs.existsSync(envPath)) {
    return;
  }

  const lines = fs.readFileSync(envPath, "utf8").split(/\r?\n/);

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) {
      continue;
    }

    const separatorIndex = trimmed.indexOf("=");
    if (separatorIndex === -1) {
      continue;
    }

    const key = trimmed.slice(0, separatorIndex).trim();
    const rawValue = trimmed.slice(separatorIndex + 1).trim();
    const value = rawValue.replace(/^["']|["']$/g, "");

    if (key && process.env[key] === undefined) {
      process.env[key] = value;
    }
  }
}

function sendJson(res, status, payload) {
  res.writeHead(status, {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
  });
  res.end(JSON.stringify(payload));
}

function collectRequestBody(req) {
  return new Promise((resolve, reject) => {
    let body = "";
    let bytes = 0;

    req.on("data", (chunk) => {
      bytes += chunk.length;
      if (bytes > MAX_BODY_BYTES) {
        reject(new Error("Request is too large. Try a shorter video or fewer frames."));
        req.destroy();
        return;
      }
      body += chunk;
    });

    req.on("end", () => resolve(body));
    req.on("error", reject);
  });
}

function toGeminiInput(messages) {
  const input = [];

  for (const message of messages || []) {
    const content = message.content;

    if (typeof content === "string") {
      input.push({ type: "text", text: content });
      continue;
    }

    if (!Array.isArray(content)) {
      continue;
    }

    for (const part of content) {
      if (part.type === "text") {
        input.push({ type: "text", text: part.text || "" });
      }

      if (part.type === "image" && part.source?.data) {
        input.push({
          type: "image",
          mime_type: part.source.media_type || "image/jpeg",
          data: part.source.data,
        });
      }
    }
  }

  return input;
}

function extractGeminiText(data) {
  if (typeof data.output_text === "string") {
    return data.output_text;
  }

  const parts = [];

  for (const step of data.steps || []) {
    for (const content of step.content || []) {
      if (typeof content.text === "string") {
        parts.push(content.text);
      }
    }

    for (const content of step.model_output?.content || []) {
      if (typeof content.text === "string") {
        parts.push(content.text);
      }
    }
  }

  for (const candidate of data.candidates || []) {
    for (const part of candidate.content?.parts || []) {
      if (typeof part.text === "string") {
        parts.push(part.text);
      }
    }
  }

  return parts.join("\n").trim();
}

function hasUsableGeminiKey() {
  return Boolean(GEMINI_API_KEY && GEMINI_API_KEY !== GEMINI_KEY_PLACEHOLDER);
}

async function analyzeWithGemini(messages) {
  if (!hasUsableGeminiKey()) {
    throw new Error("Missing GEMINI_API_KEY. Put your real Gemini key in docs/Kamran/.env before running node server.js.");
  }

  const input = toGeminiInput(messages);
  if (!input.length) {
    throw new Error("No usable text or image content was sent to the server.");
  }

  const response = await fetch("https://generativelanguage.googleapis.com/v1beta/interactions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-goog-api-key": GEMINI_API_KEY,
      "Api-Revision": "2026-05-20",
    },
    body: JSON.stringify({
      model: GEMINI_MODEL,
      input,
      store: false,
    }),
  });

  const data = await response.json();

  if (!response.ok) {
    const message = data.error?.message || `Gemini request failed with HTTP ${response.status}`;
    throw new Error(message);
  }

  const text = extractGeminiText(data);
  return text || "No response text returned by Gemini.";
}

const server = http.createServer(async (req, res) => {
  try {
    if (req.method === "OPTIONS") {
      return sendJson(res, 204, {});
    }

    if (req.method === "GET" && (req.url === "/" || req.url === "/index.html")) {
      const htmlPath = path.join(__dirname, "index.html");
      const html = fs.readFileSync(htmlPath);
      res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
      return res.end(html);
    }

    if (req.method === "GET" && req.url === "/health") {
      return sendJson(res, 200, {
        ok: true,
        model: GEMINI_MODEL,
        hasKey: hasUsableGeminiKey(),
      });
    }

    if (req.method === "POST" && req.url === "/analyze") {
      const body = await collectRequestBody(req);
      const payload = JSON.parse((body || "{}").replace(/^\uFEFF/, ""));
      const text = await analyzeWithGemini(payload.messages);

      return sendJson(res, 200, {
        content: [{ type: "text", text }],
      });
    }

    res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
    return res.end("Not found");
  } catch (error) {
    return sendJson(res, 500, {
      error: error.message || "Unexpected server error",
    });
  }
});

server.listen(PORT, () => {
  console.log("");
  console.log("Calis Gemini demo is running.");
  console.log(`Open http://localhost:${PORT}`);
  console.log(`Model: ${GEMINI_MODEL}`);
  console.log("");
});

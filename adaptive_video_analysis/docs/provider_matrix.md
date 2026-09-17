# Provider Matrix

Verified 2026-07-28 from official documentation.

| Provider/model | Role | Relevant current constraint |
|---|---|---|
| Gemini `gemini-3.6-flash` | Primary vision provider | Free tier; image/video input; structured outputs |
| Gemini `gemini-3.5-flash-lite` | Lower-cost fallback | Free tier; image/video input |
| Groq `qwen/qwen3.6-27b` | Alternate image provider | Five images per request |

Gemini video processing samples visual content at 1 FPS by default. Official
documentation estimates roughly 300 tokens per second at default media
resolution or 100 tokens per second at low resolution. This is useful as a
native-video benchmark, but 1 FPS may miss rapid exercise phases.

Groq's current free-plan documentation lists `qwen/qwen3.6-27b` at 30 requests
per minute, 1,000 requests per day, 8,000 tokens per minute, and 200,000 tokens
per day. Account limits can differ and should be read from provider response
headers or the account console.

Sources:

- https://ai.google.dev/gemini-api/docs/models/gemini-3.6-flash
- https://ai.google.dev/gemini-api/docs/pricing
- https://ai.google.dev/gemini-api/docs/video-understanding
- https://console.groq.com/docs/vision
- https://console.groq.com/docs/rate-limits
- https://github.com/google-ai-edge/mediapipe#privacy-notice


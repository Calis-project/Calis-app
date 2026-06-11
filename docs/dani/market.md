# Product Canvas: Competitor Matrix & Market Gaps

## 1. Market Overview
The fitness space is shifting from passive logging (e.g., Strava, MyFitnessPal) to active computer-vision assistance. While weightlifting has seen significant deployment, calisthenics remains highly underserved due to the complex, non-linear progression trees required for bodyweight mastery.

## 2. Competitor Benchmarking

| App / Project | Primary Tech Stack | Core Strengths | Critical Vulnerabilities / Gaps |
| :--- | :--- | :--- | :--- |
| **Calisthenics AI Coach** | Mobile CV + Conversational Agent | Directly targets bodyweight skills (planche, levers, handstands). | High latency; high processing cost; lacks deterministic safety gates. |
| **SportsReflector / Gymscore** | Advanced Skeletal Landmark Mesh | Polished 0–100 score feedback; exceptional joint angle tracking. | Focused heavily on standard barbell gym lifts; lacks calisthenics scaling models. |
| **CueForm AI / FormCheck** | Niche Custom CV Models | Hyper-accurate on specific, isolated powerlifting movements. | No holistic routine building, long-term progression tracking, or cognitive adaptability. |
| **Open-Source Indie Ecosystem** | MediaPipe + Python Streamlit apps | Free; highly hackable; great starting point for custom fork code. | Terrible UX; lacks persistent memory; no LLM context loop. |

### App Links

- **Calisthenics AI Coach:** [Apple App Store](https://apps.apple.com/us/app/calisthenics-ai-coach/id6760506157)
- **SportsReflector:** [Official website](https://sportsreflector.com/) | [Apple App Store](https://apps.apple.com/us/app/sportsreflector-ai-coach/id6759809796)
- **Gymscore:** [Apple App Store](https://apps.apple.com/us/app/gymscore-ai-fitness-coach/id6744373919) | [Google Play](https://play.google.com/store/apps/details?id=com.hypenspace.FormAI)
- **CueForm:** [Official website](https://cueform.ai/) | [Apple App Store](https://apps.apple.com/us/app/cueform-exercise-form-checker/id6450485479)
- **FormCheck AI:** [Product page](https://mwm.ai/apps/formcheck-ai-biao-ge-jian-cha/1621267448)
- **Open-source example:** [MSU-AI Form-Check on GitHub](https://github.com/MSU-AI/form-check) (abandoned and incomplete)

## 3. Our Value Proposition
1. **Calisthenics Focus:** We prioritize tendon health, leverage manipulation, and progressive bodyweight regressions over raw weight metrics.
2. **Predictable Pricing Strategy:** By parsing skeletal metrics on the edge rather than passing raw video streams to LLMs, we minimize compute costs, allowing a sustainable, scalable free tier.
3. **The Hybrid Safety Guard:** Blending unyielding geometric safety rules with the fluid encouragement of advanced cognitive conversational models.

# API

All protected endpoints require `Authorization: Bearer <JWT>`. Responses are JSON. Scores are heuristic assessments, not probabilities or proof that content is malicious. A supplied URL is never opened. It is sent to URLhaus only when `check_threat_intel` is `true`; the backend must have `URLHAUS_AUTH_KEY` configured. Results distinguish a match, no match, unavailable feed, missing key, and lookup not requested. A no-match result is not a safety guarantee. URLhaus focuses on malware-distribution URLs and does not cover every phishing or scam link.

| Method | Path | Access | Purpose |
|---|---|---|---|
| POST | `/api/auth/register` | Public | `{ "name", "email", "password" }`; returns 201 or 409 duplicate |
| POST | `/api/auth/login` | Public | `{ "email", "password" }`; returns JWT and safe user fields |
| POST | `/api/auth/forgot-password` | Public | `{ "email": "..." }`; sends a generic response and emails a one-time link if the account exists and SMTP is configured |
| POST | `/api/auth/reset-password` | Public | `{ "token": "...", "password": "..." }`; consumes an unexpired reset token |
| GET | `/api/auth/profile` | JWT | Current identity |
| POST | `/api/analysis/message` | JWT | `{ "message": "..." }` |
| POST | `/api/analysis/url` | JWT | `{ "url": "https://...", "check_threat_intel": false } (set true only with user consent to send the URL to URLhaus)` |
| GET | `/api/analysis/history?page=1&per_page=20` | JWT | Current user's paginated history |
| GET | `/api/analysis/<id>` | JWT | Owner-only report detail; other user's record returns 404 |
| POST | `/api/analysis/<id>/explanation` | JWT + explicit consent | `{ "share_with_gemini": true }`; sends that saved analysis and its signals to Gemini, returns an unsaved explanation |
| POST | `/api/assistant/chat` | JWT + explicit consent | `{ "consent_to_gemini": true, "messages": [{"role":"user|assistant", "content":"..."}] }`; sends recent turns to Gemini and returns a reply without saving the conversation |
| GET | `/api/dashboard/summary` | JWT | User-specific totals and category counts |
| GET | `/api/dashboard/recent` | JWT | Up to ten recent checks |
| GET | `/api/dashboard/threat-intelligence` | JWT | Current user's URL-check totals, URLhaus lookup outcomes and recent checks; never includes other users' data |

Successful analysis responses wrap the saved result in `analysis`, including `analysis_id`, `analysis_type`, `risk_score`, `risk_level`, `threat_type`, `indicators` with evidence, recommendations, timestamp, `detection_method`, and `model_version`. When the local SMS model is present, message analysis reports `rules+local_ml`; otherwise it uses rules only. The model adds a low-severity spam-like indicator and does not expose its internal score as a probability. It is trained on general English SMS spam data, not India-specific phishing examples.

Errors use `{ "status": "error", "message": "..." }` and appropriate HTTP codes (400 invalid input, 401 authentication, 404 inaccessible/missing record, 413 too large, 500 generic server error). Risk bands: LOW <30, MEDIUM 30–59, HIGH 60–84, CRITICAL 85–100. URL structure checks remain heuristic and are shown separately from URLhaus threat intelligence results.

The explanation endpoint requires consent on every request. It returns 503 when `GEMINI_API_KEY` is not configured and does not store the generated explanation. Configure the key and optional `GEMINI_MODEL` only in `backend/.env`; never expose the key to the browser. On the unpaid Gemini tier, prompts may be used to improve Google products and human reviewers may process them. Do not send confidential or personal information. The explanation is guidance and may be wrong.

The assistant endpoint also requires `consent_to_gemini: true` on each request. It accepts at most 21 alternating messages, each up to 3,000 characters, with a 16,000-character total context limit. CyberSahak does not persist chat messages or replies. Google processes submitted content; on the unpaid tier, prompts may be used to improve Google products and human reviewers may process them. Users should use fictional examples and never send credentials, one-time codes, or personal or confidential data. The assistant is general safety guidance, not an official report channel.

The `/report` guide creates a local draft with state/UT and district fields. A consent checkbox gates opening the government portal, but complaint details are not sent from CyberSahak and the user must complete registration and submission on the official portal. See the [official portal](https://www.cybercrime.gov.in/) and [FAQ](https://www.cybercrime.gov.in/Webform/FAQ.aspx); for financial cyber fraud the government lists 1930.

Password reset links expire after 30 minutes and can be used once. SMTP must be configured in `backend/.env`; the reset token is stored in the database as a hash. The reset request returns the same message for existing and non-existing accounts.

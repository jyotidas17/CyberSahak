# CyberSahak

CyberSahak is a Flask/PostgreSQL and React cyber safety and threat intelligence assistant for reviewing messages and URLs, with an optional Gemini-powered conversational assistant. Message checks combine explainable rules with a local supervised machine-learning signal trained on the UCI SMS Spam Collection. Users may request a Gemini explanation or chat after explicitly agreeing to send the relevant content. URL checks never open the supplied website; users can separately opt in to send a URL to URLhaus for threat intelligence. Scores are assessments, not probabilities or proof of malicious intent.

## What is implemented

- Registration, login and profile APIs with bcrypt password hashing and expiring JWTs.
- Password recovery with an emailed, single-use reset link that expires after 30 minutes. Configure SMTP variables in `backend/.env`; without SMTP settings, recovery is unavailable.
- Authenticated message and URL analysis persisted with indicators, evidence and recommendations.
- Optional URLhaus threat intelligence lookup for URLs. The URL is sent to URLhaus only when the user checks the opt-in box; otherwise only local URL rules run. A URLhaus match is evidence of a known malware-distribution URL, while a miss is not proof of safety. Configure `URLHAUS_AUTH_KEY` in `backend/.env` using a free community API key from [abuse.ch](https://auth.abuse.ch/) to enable lookups.
- A private threat intelligence dashboard that summarizes only the signed-in user's own URL checks and URLhaus results.
- A local TF-IDF plus calibrated logistic-regression SMS spam-like classifier. It is supplementary to rules and only covers general English SMS spam; it is not an India-specific phishing detector.
- Optional Gemini-powered explanation on saved analysis pages. The API key stays on the backend; analysis content is sent to Gemini only after the user checks the consent box and requests an explanation. Explanations are not saved in CyberSahak.
- An authenticated AI chat page for follow-up questions about suspicious messages, account safety, and incident response. Chat is held in browser memory, sent only after the user opts in, and is not written to the CyberSahak database.
- Authenticated history, report detail and dashboard APIs, plus React pages for analysis and a private complaint-draft guide.
- The report guide adds state/UT and district to a local draft. A consent checkbox gates opening the official portal, but CyberSahak does not transmit or submit the complaint.

The model uses the [UCI SMS Spam Collection](https://archive.ics.uci.edu/dataset/228/sms%2Bspam%2Bcollection), licensed CC BY 4.0. The train script writes the ignored model artifact and evaluation metrics under `backend/models/`.

## Run locally

### Backend

1. Use the existing Python virtual environment or create one, then install `backend/requirements.txt`.
2. Keep the existing `backend/.env`. For a new setup, copy `.env.example` to `.env` and set local database credentials and a long random `JWT_SECRET`. Never commit `.env`.
3. From `backend`, apply database migrations with `python apply_migration.py` (rerun this when a new migration is added).
4. Add `GEMINI_API_KEY` to `backend/.env` to enable the consent-gated Gemini chat and explanations. The default model is `gemini-3.5-flash-lite`; set `GEMINI_MODEL` only if you need a different supported model. Create a key in [Google AI Studio](https://aistudio.google.com/apikey). Never put this key in frontend code or commit it. Gemini's unpaid tier has quotas and may use prompts to improve Google products; human reviewers may process them. The UI warns users not to submit private, sensitive, or confidential information. Without a key, rule-based analysis still works.
5. Download the dataset and train the local model:

   ```powershell
   python scripts/download_sms_dataset.py
   python -m services.train_sms_model
   ```

   This is a one-time setup per environment. The app still works with rule-based checks if the model artifact is absent.
6. For password recovery, configure `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL`, and TLS settings in `backend/.env`. Keep mail credentials private.
7. Start the API from `backend`: `python app.py` (port 5000).

### Frontend

From `frontend`, run `npm install`, then `npm run dev`. The default API URL is `http://127.0.0.1:5000/api`; set `VITE_API_URL` at build time to use another deployment URL. Build with `npm run build`.

The MVP stores the short-lived access token in localStorage, never a password. Sign out on shared devices.

### Official complaints

For India, users can review the [National Cyber Crime Reporting Portal](https://www.cybercrime.gov.in/) and its [FAQ](https://www.cybercrime.gov.in/Webform/FAQ.aspx); the government lists **1930** for cyber financial fraud reporting. The draft includes the state/UT and district for the user's reference. The complainant must register, verify, and submit through the official portal; the app does not submit a complaint.

## Verify

From `backend`, run `python -m unittest discover -s tests -v`. The integration test connects to the configured PostgreSQL database and cleans up the unique test users it creates. From `frontend`, run `npm run build`.

See [API documentation](docs/API_DOCUMENTATION.md) and [testing notes](docs/TESTING.md).

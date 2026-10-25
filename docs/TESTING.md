# Testing

Run `python -m unittest discover -s tests -v` from `backend` with the configured PostgreSQL database available and the additive migration applied. Tests create unique accounts and remove those test accounts after the suite. Never point test configuration at an important production database.

The integration checks cover registration, duplicate prevention, login, required fields, JWT handling, protected profile, persisted message and URL results, history, dashboard counts, owner-only detail, benign and suspicious message/URL cases, optional local model metadata.

The SMS model can be retrained from `backend` with `python scripts/download_sms_dataset.py` followed by `python -m services.train_sms_model`. Training keeps separate training, threshold-selection and held-out test splits. It writes metrics to `models/sms_spam_metrics.json`; the artifact is optional and ignored by git. Its evaluation only measures general SMS spam classification and does not establish performance on Indian phishing or fraud messages.

Run the frontend production build with `npm run build` from `frontend`. Manual API checks can use routes and payloads in `API_DOCUMENTATION.md`.

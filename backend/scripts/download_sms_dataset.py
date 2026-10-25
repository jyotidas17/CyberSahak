"""Download the cited UCI SMS Spam Collection archive and validate its rows."""
import csv
import io
import ssl
import urllib.request
import zipfile
from pathlib import Path

import certifi

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "sms_spam_collection.tsv"
DATA_URL = "https://archive.ics.uci.edu/static/public/228/sms+spam+collection.zip"

tls_context = ssl.create_default_context(cafile=certifi.where())
with urllib.request.urlopen(DATA_URL, context=tls_context, timeout=60) as response:
    archive_bytes = response.read()
with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
    member = next((name for name in archive.namelist() if name.rsplit("/", 1)[-1] == "SMSSpamCollection"), None)
    if not member:
        raise RuntimeError("The UCI archive did not contain the expected SMS data file.")
    raw = archive.read(member)
text = raw.decode("utf-8")
rows = list(csv.reader(io.StringIO(text), delimiter="\t", quoting=csv.QUOTE_NONE))
if len(rows) != 5574 or any(len(row) != 2 or row[0] not in {"ham", "spam"} for row in rows):
    raise RuntimeError("The downloaded UCI data failed row-count or label validation.")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_bytes(raw)
print(f"Saved and validated {len(rows)} labeled messages to {OUTPUT.relative_to(ROOT)}")

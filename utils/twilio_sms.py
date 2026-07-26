"""
Twilio SMS integration — only sends when TWILIO_* secrets/env are configured.
Works on Streamlit when user triggers send (test or in-session alert).
Cannot push while the app is closed (no background worker on Community Cloud).
"""
from __future__ import annotations
import os
import re
from typing import Optional, Tuple
import requests

E164 = re.compile(r"^\+[1-9]\d{7,14}$")


def twilio_configured() -> bool:
    return bool(
        os.environ.get("TWILIO_ACCOUNT_SID")
        and os.environ.get("TWILIO_AUTH_TOKEN")
        and os.environ.get("TWILIO_FROM_NUMBER")
    )


def send_sms(to_number: str, body: str) -> Tuple[bool, str]:
    """Send SMS via Twilio REST API. Returns (ok, message)."""
    if not twilio_configured():
        return False, "Twilio not configured. Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER in secrets."
    to_number = (to_number or "").strip().replace(" ", "")
    if not E164.match(to_number):
        return False, "Phone must be E.164 format, e.g. +14155552671"
    body = (body or "")[:1500]
    if not body:
        return False, "Empty message"
    sid = os.environ.get("TWILIO_ACCOUNT_SID", "")
    token = os.environ.get("TWILIO_AUTH_TOKEN", "")
    from_num = os.environ.get("TWILIO_FROM_NUMBER", "")
    url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
    try:
        r = requests.post(
            url,
            data={"To": to_number, "From": from_num, "Body": body},
            auth=(sid, token),
            timeout=15,
        )
        if r.status_code in (200, 201):
            return True, "SMS sent"
        return False, f"Twilio error {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return False, f"Send failed: {e}"


SETUP_HELP = """
### Twilio setup (owner)
1. Create account at https://www.twilio.com
2. Get **Account SID** and **Auth Token**
3. Buy/verify a **From** number
4. Streamlit Secrets:
```toml
TWILIO_ACCOUNT_SID = "ACxxxxxxxx"
TWILIO_AUTH_TOKEN = "your_token"
TWILIO_FROM_NUMBER = "+1xxxxxxxxxx"
MOD_PASSWORD = "choose_a_strong_mod_password"
```
5. Users enter **E.164** phones (+1…) and request a test SMS while the app is open.

**Limit:** Community Cloud cannot text you after you close the tab without an external worker.
"""

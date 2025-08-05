
"""
sheets.py
tiny helper to append contact info to a google sheet

requires:
  • .env with:
        GSHEET_CREDS_JSON=/abs/path/to/service_account.json
        GSHEET_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
  • creds file generated from gcp → service account → json key
    share the target sheet with that service account email.
"""

from __future__ import annotations

import datetime as dt
import os
import pathlib
import sys
from typing import List

import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

# grab env vars
creds_path = os.getenv("GSHEET_CREDS_JSON")
sheet_id   = os.getenv("GSHEET_ID")
if not creds_path or not sheet_id:
    sys.exit("sheets env vars missing – add GSHEET_CREDS_JSON and GSHEET_ID to .env")

# scopes & client -------------------------------------------------
_scopes = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_file(creds_path, scopes=_scopes)
gc = gspread.authorize(creds)
ws = gc.open_by_key(sheet_id).sheet1          # first tab is enough

# public api ------------------------------------------------------
def log_contact(name: str, email: str, org: str, inquiry: str) -> None:
    """append one row with utc timestamp + contact info + question"""
    ts = dt.datetime.utcnow().isoformat(sep=" ", timespec="seconds")
    ws.append_row([ts, name, email, org, inquiry])
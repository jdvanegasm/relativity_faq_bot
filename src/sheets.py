"""
sheets.py
small helper that pushes contact info to a google sheet via user-oauth
"""

from __future__ import annotations
import datetime as dt
import os
import sys
import pathlib

import gspread
from dotenv import load_dotenv

load_dotenv()

# env vars
client_file = os.getenv("GS_CLIENT_OAUTH", "gcp_client_oauth.json")
token_file  = os.getenv("GS_TOKEN", "token.json")
sheet_id    = os.getenv("GSHEET_ID")

if not sheet_id:
    sys.exit("gsheet_id missing in .env – add it before running")

if not os.path.isabs(client_file):
    repo_root = pathlib.Path(__file__).resolve().parent.parent
    client_file = str(repo_root / client_file)

# same for token file (optional but handy)
if not os.path.isabs(token_file):
    token_file = str(pathlib.Path(__file__).resolve().parent.parent / token_file)

# oauth 
gc = gspread.oauth(
    credentials_filename=client_file,
    authorized_user_filename=token_file,
)

ws = gc.open_by_key(sheet_id).sheet1

# public gateway
def log_contact(name: str, email: str, org: str, inquiry: str) -> None:
    """append one row utc_timestamp | name | email | org | inquiry"""
    ts = dt.datetime.utcnow().isoformat(sep=" ", timespec="seconds")
    ws.append_row([ts, name, email, org, inquiry])
import os
import gspread
from dotenv import load_dotenv

load_dotenv()

gspread.oauth(
    credentials_filename=os.getenv("GS_CLIENT_OAUTH", "gcp_client_oauth.json"),
    authorized_user_filename=os.getenv("GS_TOKEN", "token.json")
)
print("oauth complete, token.json created")

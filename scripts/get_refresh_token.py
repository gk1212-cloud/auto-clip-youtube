"""Helper to obtain a YouTube OAuth refresh token (run locally, not in CI).

Usage:
  1. Download your OAuth client JSON from Google Cloud Console (Desktop app)
     and save as client_secret.json in this folder.
  2. pip install google-auth-oauthlib
  3. python scripts/get_refresh_token.py
  4. Copy the printed refresh token into the YOUTUBE_REFRESH_TOKEN secret.
"""
import os

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
creds = flow.run_local_server(port=0)
print("REFRESH TOKEN:", creds.refresh_token)
print("CLIENT ID:", creds.client_id if hasattr(creds, "client_id") else "see client_secret.json")
print("CLIENT SECRET:", creds.client_secret if hasattr(creds, "client_secret") else "see client_secret.json")

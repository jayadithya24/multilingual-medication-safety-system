"""Verify Google identity on the server; never trust browser profile fields."""
import os
from google.auth.transport.requests import Request
from google.oauth2 import id_token
from fastapi import HTTPException


def verify_google_credential(credential: str) -> dict:
    client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    if not client_id:
        raise HTTPException(503, "Google sign-in is not available yet. Use email and password.")
    try:
        claims = id_token.verify_oauth2_token(credential, Request(), client_id)
    except ValueError as error:
        raise HTTPException(401, "Google sign-in could not be verified. Please try again.") from error
    except Exception as error:
        raise HTTPException(503, "Google sign-in is temporarily unavailable. Please retry.") from error
    if (claims.get("iss") not in {"accounts.google.com", "https://accounts.google.com"}
            or claims.get("aud") != client_id or not claims.get("sub")
            or claims.get("email_verified") is not True or not claims.get("email")):
        raise HTTPException(401, "A verified Google account is required.")
    return claims

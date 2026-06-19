"""
API key authentication for mutating routes.

When API_SECRET_KEY is set in the environment, all mutating routes require a
Bearer token matching that value. When unset, auth is disabled — safe for
local single-user development but must be configured before wider deployment.

Contact Tech-AI-Engineering@derivco.com before sharing this service internally.
"""
import os
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

_bearer = HTTPBearer(auto_error=False)


def require_api_key(creds: HTTPAuthorizationCredentials = Security(_bearer)) -> None:
    expected = os.environ.get("API_SECRET_KEY", "")
    if not expected:
        return  # auth disabled — local dev only
    if not creds or creds.credentials != expected:
        raise HTTPException(401, detail="Invalid or missing API key")

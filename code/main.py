"""Simple OAuth2 Login + Role-Based Access Demo (FastAPI + Authlib)."""

import json
import os
import secrets
from pathlib import Path
from typing import Any

from authlib.integrations.base_client.errors import OAuthError
from authlib.integrations.starlette_client import OAuth
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

BASE_DIR = Path(__file__).resolve().parent

# Load .env that sits next to this file, regardless of the current working directory.
load_dotenv(BASE_DIR / ".env")

ROLES_FILE = BASE_DIR / "users_roles.json"
DEFAULT_ROLE = "student"

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
ALLOWED_DOMAIN = os.getenv("ALLOWED_DOMAIN", "").strip().lower().lstrip("@")

app = FastAPI(title="OAuth2 RBAC Demo")

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET") or secrets.token_hex(32),
    same_site="lax",
)

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

oauth = OAuth()
oauth.register(
    name="google",
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


# --------------------------------------------------------------------------- #
# Local role store
# --------------------------------------------------------------------------- #
def load_roles() -> dict[str, str]:
    """Read the email -> role mapping straight from disk on every call.

    Deliberately not cached: edits to users_roles.json take effect on the
    next request without restarting the server.
    """
    if not ROLES_FILE.exists():
        return {}
    try:
        with ROLES_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def save_roles(roles: dict[str, str]) -> None:
    with ROLES_FILE.open("w", encoding="utf-8") as f:
        json.dump(roles, f, indent=2)
        f.write("\n")


def get_or_assign_role(email: str) -> str:
    """Return the user's role, persisting new users with the default role."""
    email = email.strip().lower()
    roles = load_roles()
    if email not in roles:
        roles[email] = DEFAULT_ROLE
        save_roles(roles)
    return roles[email]


def refresh_session_role(request: Request) -> dict[str, Any] | None:
    """Re-read the user's role from disk so role edits apply on refresh."""
    user = request.session.get("user")
    if not user:
        return None

    email = (user.get("email") or "").strip().lower()
    if email:
        role = get_or_assign_role(email)
        if role != user.get("role"):
            user = {**user, "role": role}
            request.session["user"] = user
    return user


# --------------------------------------------------------------------------- #
# Reusable RBAC guard
# --------------------------------------------------------------------------- #
def require_role(*allowed_roles: str):
    """FastAPI dependency factory: 401 when unauthenticated, 403 when unauthorized."""

    async def dependency(request: Request) -> dict[str, Any]:
        user = refresh_session_role(request)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required. Please log in with Google first.",
            )
        if user.get("role") not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Access denied for role '{user.get('role')}'. "
                    f"Allowed role(s): {', '.join(allowed_roles)}."
                ),
            )
        return user

    return dependency


# --------------------------------------------------------------------------- #
# HTML error pages
# --------------------------------------------------------------------------- #
STATUS_TITLES = {
    400: "400 Bad Request",
    401: "401 Unauthorized",
    403: "403 Forbidden",
    404: "404 Not Found",
    500: "500 Internal Server Error",
}


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    message = exc.detail if isinstance(exc.detail, str) else "An unexpected error occurred."
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": exc.status_code,
            "title": STATUS_TITLES.get(exc.status_code, f"{exc.status_code} Error"),
            "message": message,
        },
        status_code=exc.status_code,
    )


# --------------------------------------------------------------------------- #
# Routes
# --------------------------------------------------------------------------- #
@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    user = refresh_session_role(request)
    return templates.TemplateResponse(request, "index.html", {"user": user})


@app.get("/login")
async def login(request: Request):
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Missing GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET in .env",
        )

    redirect_uri = request.url_for("auth")
    return await oauth.google.authorize_redirect(
        request, redirect_uri, prompt="select_account"
    )


@app.get("/auth")
async def auth(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth2 authentication failed: {e.error}",
        )

    user_info = token.get("userinfo")
    if not user_info or not user_info.get("email"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not read the email address from the Google profile.",
        )

    email = user_info["email"].strip().lower()

    if ALLOWED_DOMAIN and not email.endswith(f"@{ALLOWED_DOMAIN}"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Access denied: only @{ALLOWED_DOMAIN} Google accounts are permitted. "
                f"You signed in as {email}."
            ),
        )

    role = get_or_assign_role(email)
    request.session["user"] = {
        "name": user_info.get("name") or email,
        "email": email,
        "picture": user_info.get("picture", ""),
        "role": role,
    }
    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)


@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)


@app.get("/student-area", response_class=HTMLResponse)
async def student_area(request: Request, user: dict = Depends(require_role("student", "admin"))):
    return templates.TemplateResponse(request, "student_area.html", {"user": user})


@app.get("/admin-area", response_class=HTMLResponse)
async def admin_area(request: Request, user: dict = Depends(require_role("admin"))):
    return templates.TemplateResponse(
        request, "admin_area.html", {"user": user, "roles": load_roles()}
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

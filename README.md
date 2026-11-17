# Simple OAuth2 Login + Role-Based Access Demo

## Short Architecture Description (3–5 lines)
This project uses FastAPI as the backend server handling HTTP requests and session states. Authlib manages the OpenID Connect / OAuth2 handshake securely with Google's authorization servers. User roles ('student' or 'admin') are fetched from a local JSON datastore upon authentication, protecting endpoints via role-checking decorators/middleware.

"This project uses FastAPI for routing and session handling, with Authlib managing the OpenID Connect flow with Google. Upon authentication, a custom domain validation middleware/guard verifies that incoming email strings end strictly with @iiitnr.edu.in. Authorized institutional users are then mapped via a local JSON datastore to their respective roles ('student' or 'admin/lecturer'), protecting custom endpoints."

## Dependencies
- Python 3.9+
- FastAPI
- Uvicorn
- Authlib
- Jinja2
- Itsdangerous

## How to Run on Ubuntu (Exact Commands)

1. **Clone/Navigate to project directory and enter code folder:**
   ```bash
   cd Group_XX_OAuth2RBAC/code
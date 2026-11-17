import os
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
from database import get_user_role, set_user_role

app = FastAPI(title="OAuth2 RBAC Demo - IIITNR Secured")

# Secure session middleware
app.add_middleware(SessionMiddleware, secret_key=os.environ.get("SESSION_SECRET", "super-secret-key-change-me"))

templates = Jinja2Templates(directory="templates")

# OAuth configuration
oauth = OAuth()
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "YOUR_GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "YOUR_GOOGLE_CLIENT_SECRET")

oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    user = request.session.get('user')
    return templates.TemplateResponse("index.html", {"request": request, "user": user})

@app.get('/login')
async def login(request: Request):
    redirect_uri = request.url_for('auth')
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get('/auth')
async def auth(request: Request):
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get('userinfo')
    
    if user_info:
        email = user_info['email']
        
        # 🔒 DOMAIN RESTRICTION CHECK
        if not email.endswith("@iiitnr.edu.in"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access Denied: Only official IIITNR institutional emails (@iiitnr.edu.in) are permitted to log in."
            )
        
        role = get_user_role(email)
        request.session['user'] = {
            "name": user_info.get('name'),
            "email": email,
            "role": role
        }
    return RedirectResponse(url='/')

@app.get('/logout')
async def logout(request: Request):
    request.session.pop('user', None)
    return RedirectResponse(url='/')

@app.get('/student-area', response_class=HTMLResponse)
async def student_area(request: Request):
    user = request.session.get('user')
    if not user:
        return RedirectResponse(url='/login')
    if user['role'] not in ['student', 'admin']:
        raise HTTPException(status_code=403, detail="Access denied: Student or Lecturer role required")
    return templates.TemplateResponse("student_area.html", {"request": request, "user": user})

@app.get('/admin-area', response_class=HTMLResponse)
async def admin_area(request: Request):
    user = request.session.get('user')
    if not user:
        return RedirectResponse(url='/login')
    if user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Access denied: Lecturers/Admins only!")
    return templates.TemplateResponse("admin_area.html", {"request": request, "user": user})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
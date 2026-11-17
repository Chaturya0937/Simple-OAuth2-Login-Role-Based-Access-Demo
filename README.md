## Simple OAuth2 Login + Role-Based Access Demo

### Architecture Overview

This project uses **FastAPI** as the backend framework for handling HTTP requests, routing, and session management. **Authlib** manages the OAuth2 / OpenID Connect authentication flow with Google. After successful authentication, a custom email validation guard ensures that only users with an institutional email address ending in `@iiitnr.edu.in` can access the application. Authorized users are mapped to their respective roles (`student` or `admin/lecturer`) using a local JSON datastore. Role-based access control is then used to protect specific application endpoints.

### Technologies & Dependencies

- Python 3.9+
- FastAPI
- Uvicorn
- Authlib
- Jinja2
- Itsdangerous

---

## How to Run the Project

Follow these steps to run the project locally.

### Step 1: Clone the Repository

```bash
git clone <your-repository-url>
cd <project-folder>
```

### Step 2: Create a Virtual Environment

Create an isolated Python virtual environment:

```bash
python -m venv venv
```

### Step 3: Activate the Virtual Environment

**For Windows PowerShell:**

```powershell
.\venv\Scripts\Activate.ps1
```

**For Windows Command Prompt (CMD):**

```cmd
venv\Scripts\activate
```

**For Linux / macOS:**

```bash
source venv/bin/activate
```

### Step 4: Install Dependencies

Install all the required Python packages:

```bash
pip install -r requirements.txt
```

### Step 5: Configure Google OAuth Credentials

To enable Google Login, you need to create OAuth 2.0 credentials through the [Google Cloud Console](https://console.cloud.google.com/).

1. Create or select a Google Cloud project.
2. Configure the OAuth consent screen.
3. Create an OAuth 2.0 Client ID.
4. Select **Web application** as the application type.
5. Add the appropriate authorized redirect URI configured in your FastAPI application.

After obtaining your credentials, configure the following environment variables.

**For Windows PowerShell:**

```powershell
$env:GOOGLE_CLIENT_ID = "your-google-client-id"
$env:GOOGLE_CLIENT_SECRET = "your-google-client-secret"
```

**For Windows CMD:**

```cmd
set GOOGLE_CLIENT_ID=your-google-client-id
set GOOGLE_CLIENT_SECRET=your-google-client-secret
```

**For Linux / macOS:**

```bash
export GOOGLE_CLIENT_ID="your-google-client-id"
export GOOGLE_CLIENT_SECRET="your-google-client-secret"
```

Replace the placeholder values with your actual Google OAuth credentials.

### Step 6: Start the FastAPI Server

Run the following command:

```bash
uvicorn main:app --reload
```

### Step 7: Access the Application

Once the server starts successfully, open your browser and navigate to:

```text
http://127.0.0.1:8000
```

To access the automatically generated FastAPI API documentation, visit:

```text
http://127.0.0.1:8000/docs
```

---

## Authentication & Authorization Flow

1. **Google Login:** Users authenticate using their Google accounts.
2. **Domain Validation:** The application verifies that the authenticated email address ends with `@iiitnr.edu.in`.
3. **Role Assignment:** The user's role is retrieved from the local JSON datastore.
4. **Access Control:** Application endpoints are protected according to the assigned role.
5. **Session Management:** Authenticated user information is maintained using secure session handling.

**Note:** Only authorized institutional email accounts are permitted to access the application.
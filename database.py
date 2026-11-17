import json
import os

ROLE_DB = "users_roles.json"

def init_db():
    if not os.path.exists(ROLE_DB):
        # Default mock roles using the mandatory IIITNR domain
        default_data = {
            "student1@iiitnr.edu.in": "student",
            "lecturer1@iiitnr.edu.in": "admin"
        }
        with open(ROLE_DB, "w") as f:
            json.dump(default_data, f, indent=4)

def get_user_role(email: str) -> str:
    init_db()
    with open(ROLE_DB, "r") as f:
        data = json.load(f)
    # If an @iiitnr.edu.in user logs in for the first time, default them to 'student'
    return data.get(email, "student")

def set_user_role(email: str, role: str):
    init_db()
    with open(ROLE_DB, "r") as f:
        data = json.load(f)
    data[email] = role
    with open(ROLE_DB, "w") as f:
        json.dump(data, f, indent=4)
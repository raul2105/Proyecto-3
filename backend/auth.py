from pydantic import BaseModel
from typing import Optional, List, Dict
import datetime

class User(BaseModel):
    username: str
    password: str
    role: str # "admin", "operator", "supervisor", "quality"

class LoginRequest(BaseModel):
    username: str
    password: str

# Default Users (In-Memory DB for MVP)
INITIAL_USERS = [
    User(username="admin", password="admin123", role="admin"),
    User(username="op1", password="1234", role="operator"),
    User(username="sup1", password="sup123", role="supervisor"),
    User(username="qual1", password="qual123", role="quality"),
]

class AuthService:
    def __init__(self):
        self.users: Dict[str, User] = {u.username: u for u in INITIAL_USERS}
        self.sessions: Dict[str, str] = {} # token -> username

    def login(self, req: LoginRequest):
        user = self.users.get(req.username)
        if user and user.password == req.password:
             # Simple token strategy: just use username for MVP
             token = f"token_{user.username}_{datetime.datetime.now().timestamp()}"
             self.sessions[token] = user.username
             return {"token": token, "role": user.role, "username": user.username}
        raise Exception("Invalid credentials")

    def get_user_role(self, token: str):
        username = self.sessions.get(token)
        if username:
            return self.users[username].role
        return None

import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

ORG_URL = os.getenv("OKTA_ORG_URL")
CLIENT_ID = os.getenv("OKTA_CLIENT_ID")
CLIENT_SECRET = os.getenv("OKTA_CLIENT_SECRET")
REDIRECT_URI = os.getenv("OKTA_REDIRECT_URI")

app = FastAPI(title="IAM-Ops Portal")
app.add_middleware(SessionMiddleware, secret_key="dev-secret-change-later")

oauth = OAuth()
oauth.register(
    name="okta",
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    server_metadata_url=f"{ORG_URL}/.well-known/openid-configuration",
    client_kwargs={"scope": "openid profile email"},
)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user = request.session.get("user")
    if user:
        return f"""
        <h2>IAM-Ops Portal</h2>
        <p>Logged in as: {user.get("name")} ({user.get("email")})</p>
        <a href="/logout">Logout</a>
        """
    return """
    <h2>IAM-Ops Portal</h2>
    <a href="/login">Login with Okta</a>
    """


@app.get("/login")
async def login(request: Request):
    return await oauth.okta.authorize_redirect(request, REDIRECT_URI)


@app.get("/authorization-code/callback")
async def callback(request: Request):
    token = await oauth.okta.authorize_access_token(request)
    user = token.get("userinfo")
    request.session["user"] = dict(user)
    return RedirectResponse(url="/")


@app.get("/logout")
async def logout(request: Request):
    request.session.pop("user", None)
    return RedirectResponse(url="/")

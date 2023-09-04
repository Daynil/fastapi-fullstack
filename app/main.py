import uvicorn
from fastapi import FastAPI, Request
from starlette.authentication import (
    AuthenticationBackend,
    AuthCredentials,
)
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.requests import HTTPConnection
from starlette.responses import RedirectResponse
from starlette.staticfiles import StaticFiles

from app import build
from app.api_router import app_router
from app.config import protected_routes, generated_path
from app.models import AppUser
from app.pocketbase.pocketbase_api import PocketbaseAPI
from app.util.utilities import cprint, CColors

app = FastAPI(title="fastapi-fullstack")


class PocketbaseAuthBackend(AuthenticationBackend):
    async def authenticate(self, conn: HTTPConnection):
        if "token" not in conn.cookies:
            return AuthCredentials([]), AppUser()

        try:
            user = PocketbaseAPI.send_request(
                "POST",
                "/collections/users/auth-refresh",
                headers={"Authorization": conn.cookies["token"]},
            ).data
        except Exception as e:
            return AuthCredentials([]), AppUser()

        return AuthCredentials(["authenticated"]), AppUser(
            id=user["record"]["id"],
            username=user["record"]["username"],
            email=user["record"]["email"],
            token=user["token"],
        )


@app.middleware("http")
async def authenticate_user(request: Request, call_next):
    if request.url.path in protected_routes and not request.user.is_authenticated:
        return RedirectResponse("/login.html")
    return await call_next(request)


# ***NOTE*** This must come *after* the authenticate_user fastapi middleware
app.add_middleware(AuthenticationMiddleware, backend=PocketbaseAuthBackend())


app.include_router(app_router, prefix="/app")
# app.mount(
#     "/static",
#     StaticFiles(directory=Path(__file__).parent / "static"),
#     name="static",
# )
app.mount(
    "/",
    StaticFiles(directory=generated_path, html=True),
    name="generated",
)


def start():
    # Can debug with this, but need to run with `uvicorn app.main:app --reload` to get autoreload and colors
    cprint("Rebuilding...!", CColors.WARNING)
    build.start()
    cprint("Build complete!", CColors.OKGREEN)
    uvicorn.run("app.main:app")


if __name__ == "__main__":
    start()

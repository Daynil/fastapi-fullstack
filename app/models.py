from typing import Literal

from pydantic import BaseModel
from starlette.authentication import BaseUser
from starlette.requests import Request


class AppUser(BaseModel, BaseUser):
    id: str = ""
    username: str = ""
    email: str = ""
    token: str = ""

    @property
    def is_authenticated(self) -> bool:
        return self.email != ""

    @property
    def display_name(self) -> str:
        return self.username


class RequestAuthed(Request):
    user: AppUser


class AlertInfo(BaseModel):
    type: Literal["good", "bad", "alert", "info"]
    title: str
    message: str

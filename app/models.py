from typing import Literal, TypedDict

from pydantic import BaseModel
from starlette.authentication import BaseUser
from starlette.requests import Request

from app.pocketbase.generated_types import Books, Locations


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


class AppError(Exception):
    """
    Raise for errors we know about and have meaningful messages
    to pass back to callers.
    """


class AlertInfo(BaseModel):
    type: Literal["good", "bad", "alert", "info"]
    title: str
    message: str


class BooksLocations(Books):
    class Expand(BaseModel):
        location: Locations

    expand: Expand | None = None

from typing import Annotated

from fastapi import APIRouter, Form
from starlette.requests import Request
from starlette.responses import Response

from app.models import RequestAuthed, AlertInfo
from app.pocketbase.pocketbase_api import PocketbaseAPI
from app.util.template_helpers import info_banner, page_response

app_router = APIRouter()


@app_router.get("/test")
async def test():
    return {"message": "Success!!!"}


@app_router.get("/books")
async def books(
    request: RequestAuthed,
):
    # to get admin token:
    # admin = PocketbaseAPI.send_request(
    #     "POST",
    #     "/admins/auth-with-password",
    #     json={"identity": "dlibinrx@gmail.com", "password": "adminpass"},
    # )

    all_books = PocketbaseAPI.send_request(
        "GET",
        "/collections/books/records",
        headers={"Authorization": request.user.token},
    ).data

    return page_response(
        "books/books.html",
        request,
        context={
            "books": [
                book for book in all_books["items"] if book["user"] != request.user.id
            ],
            "user_books": [
                book for book in all_books["items"] if book["user"] == request.user.id
            ],
        },
    )


@app_router.post("/books/{book_id}")
async def add_book(request: RequestAuthed, book_id: str):
    try:
        _ = PocketbaseAPI.send_request(
            "PATCH",
            f"/collections/books/records/{book_id}",
            headers={"Authorization": request.user.token},
            json={"user": request.user.id},
        ).data
    except Exception as e:
        print(e)

    all_books = PocketbaseAPI.send_request(
        "GET",
        "/collections/books/records",
        headers={"Authorization": request.user.token},
    ).data

    return page_response(
        "books/book_list.html",
        request,
        context={
            "books": [
                book for book in all_books["items"] if book["user"] != request.user.id
            ],
            "user_books": [
                book for book in all_books["items"] if book["user"] == request.user.id
            ],
        },
    )


@app_router.delete("/books/{book_id}")
async def delete_book(request: RequestAuthed, book_id: str):
    _ = PocketbaseAPI.send_request(
        "PATCH",
        f"/collections/books/records/{book_id}",
        headers={"Authorization": request.user.token},
        json={"user": None},
    ).data

    all_books = PocketbaseAPI.send_request(
        "GET",
        "/collections/books/records",
        headers={"Authorization": request.user.token},
    ).data

    return page_response(
        "books/book_list.html",
        request,
        context={
            "books": [
                book for book in all_books["items"] if book["user"] != request.user.id
            ],
            "user_books": [
                book for book in all_books["items"] if book["user"] == request.user.id
            ],
        },
    )


@app_router.get("/auth_menu")
async def auth_menu(request: Request):
    return page_response("auth_menu.html", request)


@app_router.post("/login")
async def login(
    request: Request,
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
):
    try:
        user = PocketbaseAPI.send_request(
            "POST",
            "/collections/users/auth-with-password",
            json={"identity": email, "password": password},
        )
    except Exception as e:
        # if e.args[0]["code"] == 400:
        return info_banner(
            request,
            AlertInfo(
                type="bad",
                title="Login error",
                message="Please check your information and try again.",
            ),
        )

    response = Response(headers={"HX-Redirect": "/app/books"}, status_code=200)
    response.set_cookie(
        "token", user.data["token"], secure=True, httponly=True, samesite="strict"
    )
    return response


@app_router.post("/logout")
async def logout(request: Request):
    response = Response(headers={"HX-Redirect": "/"}, status_code=200)
    if request.cookies["token"]:
        response.delete_cookie("token", secure=True, httponly=True, samesite="strict")
    return response

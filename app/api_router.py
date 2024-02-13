from typing import Annotated

from fastapi import APIRouter, Form
from starlette.requests import Request
from starlette.responses import Response

from app.models import AlertInfo, RequestAuthed
from app.pocketbase.pocketbase_api import PocketbaseAPI
from app.util.template_helpers import (
    html_block_response,
    html_macro_response,
    html_page_response,
    html_response,
    info_banner,
    render_template_macro,
)

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

    return html_page_response(
        "books/page.jinja",
        request,
        context={"books": all_books["items"]},
    )


@app_router.get("/books/list")
async def books_list(
    request: RequestAuthed,
):
    all_books = PocketbaseAPI.send_request(
        "GET",
        "/collections/books/records",
        headers={"Authorization": request.user.token},
    ).data

    return html_macro_response(
        "books/book_list.jinja",
        context={"books": all_books["items"], "user_id": request.user.id},
    )


@app_router.patch("/books/{book_id}")
async def grab_book(request: RequestAuthed, book_id: str):
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

    return html_macro_response(
        "books/book_list.jinja",
        context={"books": all_books["items"], "user_id": request.user.id},
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

    return html_macro_response(
        "books/book_list.jinja",
        context={"books": all_books["items"], "user_id": request.user.id},
    )


@app_router.post("/books")
async def add_book(
    request: RequestAuthed,
    title: Annotated[str, Form()],
    author: Annotated[str, Form()],
):
    # Simulated error
    if title == "error":
        alert = AlertInfo(
            type="bad",
            title="Test error",
            message="This error was a test.",
        )
        return html_block_response(
            "books/page.jinja",
            block_name="add_book_form",
            request=request,
            context={"error": alert},
        )

    _ = PocketbaseAPI.send_request(
        "POST",
        "/collections/books/records/",
        headers={"Authorization": request.user.token},
        json={"title": title, "author": author, "user": request.user.id},
    ).data

    return html_block_response(
        "books/page.jinja",
        block_name="add_book_form",
        request=request,
        headers={"HX-Trigger": "newBook"},
    )


@app_router.get("/auth_menu")
async def auth_menu(request: Request):
    return html_page_response("auth_menu.jinja", request)


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
        # TODO: different errors depeding on pocketbase response (see rxverisure)
        return info_banner(
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

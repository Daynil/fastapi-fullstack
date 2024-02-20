from typing import Annotated

from fastapi import APIRouter, Form
from starlette.requests import Request
from starlette.responses import Response

from app.auth import create_user, login_user
from app.models import AlertInfo, AppError, BooksLocations, RequestAuthed
from app.pocketbase.generated_types import (
    Books,
    BooksCreate,
    BooksUpdate,
    Collections,
    Users,
)
from app.pocketbase.pocketbase_api import (
    PocketbaseAPI,
    create_record,
    delete_record,
    find_records,
    update_record,
)
from app.util.template_helpers import (
    html_template_response,
    info_banner,
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

    res = await find_records(
        Collections.books,
        model=BooksLocations,
        token=request.user.token,
        expand="location",
    )

    return html_template_response(
        "books/page.jinja",
        request,
        context={"books": res.items},
    )


@app_router.get("/books/list")
async def books_list(
    request: RequestAuthed,
):
    res = await find_records(
        Collections.books, model=Books, token=request.user.token, expand="locations"
    )

    return html_template_response(
        "books/book_list.jinja",
        macro_name=".",
        context={"books": res.items, "user_id": request.user.id},
    )


@app_router.patch("/books/{book_id}")
async def grab_book(request: RequestAuthed, book_id: str):
    try:
        _ = await update_record(
            Collections.books,
            id=book_id,
            model=Books,
            updates=BooksUpdate(user=request.user.id),
        )
    except Exception as e:
        print(e)

    res = await find_records(Collections.books, model=Books, token=request.user.token)

    return html_template_response(
        "books/book_list.jinja",
        macro_name=".",
        context={"books": res.items, "user_id": request.user.id},
    )


@app_router.delete("/books/{book_id}")
async def delete_book(request: RequestAuthed, book_id: str):
    _ = await update_record(
        Collections.books, id=book_id, updates=BooksUpdate(user=None)
    )

    res = await find_records(Collections.books, model=Books, token=request.user.token)

    return html_template_response(
        "books/book_list.jinja",
        macro_name=".",
        context={"books": res.items, "user_id": request.user.id},
    )


@app_router.post("/books")
async def add_book(
    request: RequestAuthed,
    title: Annotated[str, Form()],
    author: Annotated[str, Form()],
):
    # Simulated error
    # TODO: make error on duplicate (from pocketbase)
    if title == "error":
        alert = AlertInfo(
            type="bad",
            title="Test error",
            message="This error was a test.",
        )
        return html_template_response(
            "books/page.jinja",
            block_name="add_book_form",
            request=request,
            context={"error": alert},
        )

    _ = await create_record(
        Collections.books, BooksCreate(title=title, author=author, user=request.user.id)
    )

    return html_template_response(
        "books/page.jinja",
        block_name="add_book_form",
        request=request,
        headers={"HX-Trigger": "newBook"},
    )


@app_router.get("/auth_menu")
async def auth_menu(request: Request):
    return html_template_response("auth_menu.jinja", request)


@app_router.post("/login")
async def login(
    request: Request,
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
):
    try:
        user = await login_user(email, password)
    except AppError as e:
        return info_banner(
            AlertInfo(
                type="bad",
                title="Login error",
                message="Please check your information and try again.",
            ),
        )
    except Exception as e:
        return info_banner(
            AlertInfo(
                type="bad",
                title="Server error",
                message="Please try again later.",
            ),
        )

    response = Response(headers={"HX-Redirect": "/app/books"}, status_code=200)
    response.set_cookie(
        "token", user.data["token"], secure=True, httponly=True, samesite="strict"
    )
    return response


@app_router.post("/signup")
async def signup(
    request: Request,
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
    password_confirm: Annotated[str, Form()],
):
    try:
        user = await create_user(email, password, password_confirm)
    except AppError as e:
        return info_banner(
            AlertInfo(
                type="bad",
                title="Signup error",
                message=str(e),
            ),
        )
    except Exception as e:
        return info_banner(
            AlertInfo(
                type="bad",
                title="Server error",
                message="Please try again later.",
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

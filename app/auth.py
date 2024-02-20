from traceback import print_exc

from app.models import AppError
from app.pocketbase.pocketbase_api import (
    PocketbaseAPI,
    parse_error,
)


async def login_user(email: str, password: str):
    try:
        user = await PocketbaseAPI.send_request_async(
            "POST",
            "/collections/users/auth-with-password",
            json={"identity": email, "password": password},
        )
        return user
    except Exception as e:
        pe = parse_error(e)
        if pe.code == 400:
            raise AppError(pe.message)
        raise e


async def create_user(email: str, password: str, password_confirm: str):
    try:
        _ = await PocketbaseAPI.send_request_async(
            "POST",
            "/collections/users/records",
            json={
                "email": email,
                "password": password,
                "passwordConfirm": password_confirm,
            },
        )
        return await login_user(email, password)
    except Exception as e:
        pe = parse_error(e)
        if (
            pe.data.get("email")
            and pe.data["email"]["code"] == "validation_invalid_email"
        ):
            raise AppError(pe.data["email"]["message"])
        elif (
            pe.data.get("password")
            and pe.data["password"]["code"] == "validation_length_out_of_range"
        ):
            raise AppError(pe.data["password"]["message"].replace("The", "Password"))
        elif (
            pe.data.get("passwordConfirm")
            and pe.data["passwordConfirm"]["code"] == "validation_values_mismatch"
        ):
            raise AppError(
                pe.data["passwordConfirm"]["message"].replace("Values", "Passwords")
            )
        raise e

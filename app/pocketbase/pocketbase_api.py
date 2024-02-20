import json
from typing import Generic, Type, TypeVar

from pydantic import BaseModel
from rich import print as rprint

from app.config import app_path
from app.pocketbase.db import Sqlite
from app.pocketbase.generated_types import Collections
from app.util.client import ApiClient

T = TypeVar("T")

PocketbaseAPI = ApiClient("http://127.0.0.1:8090/api", use_async=True)
pb_db = Sqlite(app_path / "pocketbase" / "pb_data" / "data.db")


class PocketbaseError(Exception):
    """
    Raise for errors we know about and have meaningful messages
    to pass back to callers.
    """

    code: int
    message: str
    data: dict

    def __init__(self, code: int, message: str, data) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data


class PaginatedRes(BaseModel, Generic[T]):
    page: int
    perPage: int
    totalItems: int
    totalPages: int
    items: list[T]


def parse_error(e: Exception):
    return PocketbaseError(e.args[0]["code"], e.args[0]["message"], e.args[0]["data"])


async def find_records(
    collection: Collections,
    model: Type[T] | None = None,
    token="",
    page=1,
    per_page=30,
    sort="",
    filter="",
    expand="",
    fields="",
    skip_total=False,
) -> PaginatedRes[T]:
    url = f"/collections/{collection}/records?page={page}&perPage={per_page}&filter={filter}&sort={sort}&expand={expand}&fields={fields}&skipTotal={skip_total}"
    res = await PocketbaseAPI.send_request_async(
        "GET",
        url,
        headers={"Authorization": token},
    )
    data = PaginatedRes(**res.data)
    if model:
        data.items = [model(**item) for item in data.items]
    return data


async def find_record(
    collection: Collections,
    id: str,
    updates: BaseModel,
    model: Type[T] | None = None,
    token="",
    expand="",
    fields="",
) -> T:
    url = f"/collections/{collection}/records/{id}?expand={expand}&fields={fields}"
    res = await PocketbaseAPI.send_request_async(
        "GET",
        url,
        headers={"Authorization": token},
        json=updates.model_dump(exclude_unset=True),
    )
    data = res.data
    if model:
        data = model(**data)
    return data


async def update_record(
    collection: Collections,
    id: str,
    updates: BaseModel,
    model: Type[T] | None = None,
    token="",
    expand="",
    fields="",
) -> T:
    url = f"/collections/{collection}/records/{id}?expand={expand}&fields={fields}"
    res = await PocketbaseAPI.send_request_async(
        "PATCH",
        url,
        headers={"Authorization": token},
        json=updates.model_dump(exclude_unset=True),
    )
    data = res.data
    if model:
        data = model(**data)
    return data


async def delete_record(
    collection: Collections,
    id: str,
    token="",
):
    url = f"/collections/{collection}/records/{id}"
    _ = await PocketbaseAPI.send_request_async(
        "DELETE",
        url,
        headers={"Authorization": token},
    )


async def create_record(
    collection: Collections,
    record: BaseModel,
    model: Type[T] | None = None,
    token="",
    expand="",
    fields="",
) -> T:
    url = f"/collections/{collection}/records?expand={expand}&fields={fields}"
    res = await PocketbaseAPI.send_request_async(
        "POST",
        url,
        headers={"Authorization": token},
        json=record.model_dump(exclude_unset=True),
    )
    data = res.data
    if model:
        data = model(**data)
    return data


type_map = {
    "text": "str",
    "number": "int | float",
    "bool": "bool",
    "relation": "str",
    "file": "str",
}


base_system_fields = """
class BaseSystemFields(BaseModel):
    id: str
    created: str
    updated: str

class BaseSystemFieldsUpdate(BaseModel):
    id: str | None = None
    created: str | None = None
    updated: str | None = None


class AuthSystemFields(BaseSystemFields):
    email: str
    emailVisibility: bool
    username: str
    verified: bool

    
class AuthSystemFieldsUpdate(BaseSystemFieldsUpdate):
    email: str | None = None
    emailVisibility: bool | None = None
    username: str | None = None
    verified: bool | None = None
""".strip()


def introspect_pocketbase_types():
    res = pb_db.execute("select distinct name from _collections")

    # gen_type_str = f"from pydantic import BaseModel\n\n\n{base_system_fields}\n\n\n"
    gen_type_str = "from enum import StrEnum\n\nfrom pydantic import BaseModel\n\n\nclass Collections(StrEnum):\n"
    for name in res.fetchall():
        collection = name[0]
        gen_type_str += f'    {collection} = "{collection}"\n'

    res = pb_db.execute("select type, name, schema from _collections")

    gen_type_str += f"\n\n{base_system_fields}\n\n\n"
    for collection_type, name, schema in res.fetchall():
        gen_type_str += f"class {name.capitalize()}({'AuthSystemFields' if collection_type == 'auth' else 'BaseSystemFields'}):\n"
        schema = json.loads(schema)
        for column in schema:
            gen_type_str += f"    {column['name']}: {type_map[column['type']]}"
            if not column["required"]:
                gen_type_str += " | None = None\n"
            else:
                gen_type_str += "\n"

        gen_type_str += "\n\n"

        gen_type_str += f"class {name.capitalize()}Create({'AuthSystemFieldsUpdate' if collection_type == 'auth' else 'BaseSystemFieldsUpdate'}):\n"
        for column in schema:
            gen_type_str += f"    {column['name']}: {type_map[column['type']]}"
            if not column["required"]:
                gen_type_str += " | None = None\n"
            else:
                gen_type_str += "\n"

        gen_type_str += "\n\n"

        gen_type_str += f"class {name.capitalize()}Update({'AuthSystemFieldsUpdate' if collection_type == 'auth' else 'BaseSystemFieldsUpdate'}):\n"
        for column in schema:
            gen_type_str += (
                f"    {column['name']}: {type_map[column['type']]} | None = None\n"
            )

        gen_type_str += "\n\n"

    with open(app_path / "pocketbase" / "generated_types.py", "w+") as f:
        f.write(gen_type_str.rstrip() + "\n")


if __name__ == "__main__":
    introspect_pocketbase_types()

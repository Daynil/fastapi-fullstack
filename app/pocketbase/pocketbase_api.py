import json

from app.config import app_path
from app.pocketbase.db import Sqlite
from app.util.client import ApiClient

PocketbaseAPI = ApiClient("http://127.0.0.1:8090/api")
pb_db = Sqlite(app_path / "pocketbase" / "pb_data" / "data.db")

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


class AuthSystemFields(BaseSystemFields, BaseModel):
    email: str
    emailVisibility: bool
    username: str
    verified: bool
""".strip()


def introspect_pocketbase_types():
    res = pb_db.execute("select type, name, schema from _collections")

    gen_type_str = f"from pydantic import BaseModel\n\n\n{base_system_fields}\n\n\n"
    for collection_type, name, schema in res.fetchall():
        gen_type_str += f"class {name.capitalize()}({'AuthSystemFields' if collection_type == 'auth' else 'BaseSystemFields'}, BaseModel):\n"
        schema = json.loads(schema)
        for column in schema:
            gen_type_str += f"    {column['name']}: {type_map[column['type']]}"
            if not column["required"]:
                gen_type_str += " | None\n"
            else:
                gen_type_str += "\n"

        gen_type_str += "\n\n"

    with open(app_path / "pocketbase" / "generated_types.py", "w+") as f:
        f.write(gen_type_str)


if __name__ == "__main__":
    introspect_pocketbase_types()

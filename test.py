from app.config import jinja_env
from app.pocketbase.pocketbase_api import introspect_pocketbase_types


def test():
    template = jinja_env.get_template("books/page.jinja")
    block_render_func = template.blocks["add_book_form"]
    pass


if __name__ == "__main__":
    introspect_pocketbase_types()

from app.config import jinja_env


def test():
    template = jinja_env.get_template("books/page.jinja")
    block_render_func = template.blocks["add_book_form"]
    pass


if __name__ == "__main__":
    test()

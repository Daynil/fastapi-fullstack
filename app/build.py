from os import makedirs
from shutil import copytree, rmtree, ignore_patterns

from app.config import (
    templates,
    to_generate_path,
    generated_path,
    main_menu,
    static_path,
)


def start(clean=False):
    """
    Build project.
    :param clean: If clean build, clear static libs (/lib) and rebuild.
    Otherwise, always leave lib cached and don't rebuild. These are large files not likely to change often.
    :return:
    """
    if clean and generated_path.exists():
        rmtree(generated_path)

    makedirs(generated_path, exist_ok=True)

    copytree(
        static_path,
        generated_path,
        dirs_exist_ok=True,
        ignore=None if clean else ignore_patterns("lib/*"),
    )

    for path in to_generate_path.rglob("*.html"):
        with generated_path.joinpath(path.name).open("w", encoding="utf-8") as f:
            f.write(
                templates.get_template(f"to_pregenerate/{path.name}").render(
                    main_menu=main_menu
                )
            )


if __name__ == "__main__":
    start(clean=True)

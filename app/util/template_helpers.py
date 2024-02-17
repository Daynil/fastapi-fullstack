import re
from typing import Any, Mapping

from fastapi import Response
from starlette.requests import Request

from app.config import jinja_env, main_menu
from app.models import AlertInfo

# When mounted under "/app" routes call "app/lib" for static content instead of "/lib"
base_context = {"base_path_reset": "../", "main_menu": main_menu}


def _render_template_block(template_name: str, block_name: str, context=None):
    if context is None:
        context = {}

    template = jinja_env.get_template(template_name)
    block_render_func = template.blocks[block_name]

    context = template.new_context(context)
    return jinja_env.concat([n for n in block_render_func(context)])


def _render_template_macro(template_name: str, macro_name="", context=None) -> str:
    """
    Renders the result of the macro inside a jinja template.
    This is effectively the same as render_template, but with a macro.
    Allows me to render macros either within another template, or separately.

    Args:
        template_name: Path to template, e.g. components/info_banner.jinja
        macro_name: Name of the macro in the component. If not passed, or if '.'
          uses the file name as the macro name by convention (e.g. info_banner)
        context: Arguments to pass to the macro.

    Returns:
        Rendered html string of the template.
    """

    if context is None:
        context = {}

    module = _template_macro(template_name)

    if macro_name and macro_name != ".":
        function_name = macro_name
    else:
        # Template names include path of the folder they are in, if any
        # So we need to split out just the file name without extension:
        # components/info_banner.jinja -> info_banner
        # By my convention, this is the module's macro name as well
        function_name_match = re.search(r"([^\s\/]+).jinja", template_name)

        if not function_name_match:
            raise Exception("Invalid template module name.")

        function_name = function_name_match.group(1)

    module_function = getattr(module, function_name)
    return module_function(**context)


def _template_macro(template_name: str) -> Any:
    """
    Simple helper to get a jinja template as a module to allow the rendering
    of individual macros to a template.

    Cast to any to ignore type error when calling macros.

    Example:
    ```python
    _template_macro('macro_file.jinja').macro_name(macro_variable)
    ```
    """
    return jinja_env.get_template(template_name).module


def render_template(
    template_name: str,
    request: Request | None = None,
    block_name="",
    macro_name="",
    context=None,
):
    """
    High level convenience function to render a jinja template to a string.
    This string can then be used directly in an HTML response, or combined with
    other rendered jinja template strings to form a complete response.

    Args:
        template_name: Path to template file, e.g. components/info_banner.jinja
        request: The request object from an HTTP request.
        block_name: If present, renders only the named block in the template file.
        macro_name: If present, renders only the named macro in the template file (pass '.' to use file name as macro name e.g. books/book_list.jinja -> book_list).
        context: Dict of all variables needed to render the template (or variables for the macro).

    Returns:
        Rendered string
    """
    if context is None:
        context = {}

    if request:
        context = {**context, "request": request}

    # Macros do not take base context, so return first if macro
    if macro_name:
        return _render_template_macro(template_name, macro_name, context)

    context = {**base_context, **context}

    if block_name:
        return _render_template_block(template_name, block_name, context)

    return jinja_env.get_template(template_name).render(context)


def html_response(
    content: str,
    status_code: int = 200,
    media_type: str = "text/html",
    headers: Mapping[str, str] | None = None,
):
    """Create an HTML response from a plain HTML string.

    Returns:
        HTML Response, which can be passed directly to the client.
    """
    return Response(
        content, status_code=status_code, media_type=media_type, headers=headers
    )


def html_template_response(
    template_name: str,
    request: Request | None = None,
    block_name="",
    macro_name="",
    context=None,
    status_code: int = 200,
    media_type: str = "text/html",
    headers: Mapping[str, str] | None = None,
):
    """
    Convenience wrapper to both render_template and return a full HTML response.

    Args:
        template_name: Path to template file, e.g. components/info_banner.jinja
        request: The request object from an HTTP request.
        block_name: If present, renders only the named block in the template file.
        macro_name: If present, renders only the named macro in the template file (pass '.' to use file name as macro name e.g. books/book_list.jinja -> book_list).
        context: Dict of all variables needed to render the template (or variables for the macro).

    Returns:
        HTML Response, which can be passed directly to the client.
    """
    if context is None:
        context = {}

    if request:
        context = {**context, "request": request}

    return html_response(
        render_template(
            template_name,
            block_name=block_name,
            macro_name=macro_name,
            context=context,
        ),
        status_code=status_code,
        media_type=media_type,
        headers=headers,
    )


def info_banner(alert: AlertInfo):
    """Convenience wrapper for info banner component. This allows me to
    specify the type of the context

    Returns:
      HTML Response, which can be passed directly to the client.
    """
    return html_template_response(
        "components/info_banner.jinja", context={"alert": alert}
    )

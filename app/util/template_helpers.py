import json
import re
from typing import Any, Mapping, Optional

from fastapi import Response
from starlette.requests import Request

from app.config import jinja_env, main_menu
from app.models import AlertInfo

# When mounted under "/app" routes call "app/lib" for static content instead of "/lib"
base_context = {"base_path_reset": "../", "main_menu": main_menu}


def _render_template(template_name: str, context=None):
    if context is None:
        context = {}
    return jinja_env.get_template(template_name).render({**base_context, **context})


def _render_template_block(template_name: str, block_name: str, context=None):
    if context is None:
        context = {}

    template = jinja_env.get_template(template_name)
    block_render_func = template.blocks[block_name]

    context = template.new_context(context)
    return jinja_env.concat([n for n in block_render_func(context)])


def render_template_macro(template_name: str, context=None) -> str:
    """
    Renders the result of the macro inside a jinja template.
    This is effectively the same as render_template, but with a macro.
    Allows me to render macros either within another template, or separately.

    Args:
        template_name: Path to template, e.g. components/info_banner.jinja
        context: Arguments to pass to the macro.

    Returns:
        Rendered html string of the template.
    """

    if context is None:
        context = {}

    module = _template_macro(template_name)

    # Template names include path of the folder they are in, if any
    # So we need to split out just the file name without extension:
    # components/info_banner.jinja -> info_banner
    # By my convention, this is the module's macro name as well
    function_name = re.search(r"([^\s\/]+).jinja", template_name)

    if not function_name:
        raise Exception("Invalid template module name.")

    module_function = getattr(module, function_name.group(1))
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


def html_macro_response(
    template_name: str,
    context=None,
    status_code: int = 200,
    media_type: str = "text/html",
    headers: Mapping[str, str] | None = None,
):
    """Create an HTML response from the contents of an macro file.

    Args:
        template_name: Note template name and macro name must match.
        context: Context in this case is the arguments to the macro.

    Returns:
        HTML Response, which can be passed directly to the client.
    """
    return html_response(
        render_template_macro(template_name, context),
        status_code=status_code,
        media_type=media_type,
        headers=headers,
    )


def html_block_response(
    template_name: str,
    block_name: str,
    request: Request,
    context=None,
    status_code: int = 200,
    media_type: str = "text/html",
    headers: Mapping[str, str] | None = None,
):
    """Create an HTML response from the a jinja template block, pulling
    just the block out from the main template.

    Args:
        template_name:
        context: Context in this case is all the variables used in all components.

    Returns:
        HTML Response, which can be passed directly to the client.
    """
    if context is None:
        context = {}
    return html_response(
        _render_template_block(
            template_name, block_name, {**context, "request": request}
        ),
        status_code=status_code,
        media_type=media_type,
        headers=headers,
    )


def html_page_response(
    template_name: str,
    request: Request,
    context=None,
    status_code: int = 200,
    media_type: str = "text/html",
    headers: Mapping[str, str] | None = None,
):
    """Create an HTML response from the a jinja template.

    Args:
        template_name:
        context: Context in this case is all the variables used in all components.

    Returns:
        HTML Response, which can be passed directly to the client.
    """
    if context is None:
        context = {}
    return html_response(
        _render_template(template_name, {**context, "request": request}),
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
    return html_macro_response("components/info_banner.jinja", context={"alert": alert})

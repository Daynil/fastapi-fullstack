import re
from typing import Any, Mapping, Optional

from fastapi import Response
from starlette.requests import Request

from app.config import jinja_env, main_menu, templates
from app.models import AlertInfo

# When mounted under "/app" routes call "app/lib" for static content instead of "/lib"
base_context = {"base_path_reset": "../", "main_menu": main_menu}


def render_template(template_name: str, context=None):
    if context is None:
        context = {}
    return jinja_env.get_template(template_name).render({**base_context, **context})


def render_template_module(template_name: str, context=None) -> str:
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

    module = template_module(template_name)

    # Template names include path of the folder they are in, if any
    # So we need to split out just the file name without extension:
    # components/info_banner.jinja -> info_banner
    # By my convention, this is the module's macro name as well
    function_name = re.search(r"([^\s\/]+).jinja", template_name)

    if not function_name:
        raise Exception("Invalid template module name.")

    module_function = getattr(module, function_name.group(1))
    return module_function(**context)


def template_module(template_name: str) -> Any:
    """
    Simple helper to get a jinja template as a module to allow the rendering
    of individual macros to a template.

    Cast to any to ignore type error when calling macros.

    Example:
    ```python
    template_module('macro_file.jinja').macro_name(macro_variable)
    ```
    """
    return jinja_env.get_template(template_name).module


def html_response(
    content: str,
    status_code: int = 200,
    media_type: str = "text/html",
    headers: Mapping[str, str] | None = None,
):
    return Response(
        content, status_code=status_code, media_type=media_type, headers=headers
    )


def page_response(
    template_name: str,
    request: Request,
    context=None,
    status_code: int = 200,
    media_type: str = "text/html",
    headers: Mapping[str, str] | None = None,
):
    if context is None:
        context = {}
    return html_response(
        render_template(template_name, {**context, "request": request}),
        status_code=status_code,
        media_type=media_type,
        headers=headers,
    )


# def info_banner(request: Request, alert: AlertInfo):
#     return templates.TemplateResponse(
#         "components/info_banner.jinja",
#         {
#             **base_context,
#             "request": request,
#             "alert": alert,
#         },
#     )


def info_banner(alert: AlertInfo):
    return html_response(
        template_module("components/info_banner.jinja").info_banner(alert),
        # status_code=500 if alert.type == "bad" else 200,
    )

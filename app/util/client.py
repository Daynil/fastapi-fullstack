import json as json_lib
import re
from dataclasses import dataclass
from typing import Any, Generator, Generic, Literal, Optional, Type, TypeVar

import httpx
from httpx._client import USE_CLIENT_DEFAULT, UseClientDefault
from httpx._types import (
    CookieTypes,
    HeaderTypes,
    QueryParamTypes,
    RequestContent,
    RequestData,
    RequestExtensions,
    RequestFiles,
    TimeoutTypes,
    URLTypes,
)
from pydantic import BaseModel

T = TypeVar("T")


@dataclass
class APIResponse(Generic[T]):
    response: httpx.Response
    data: T


class ApiClient:
    auth_token: str
    async_client: httpx.AsyncClient
    client: httpx.Client

    def __init__(
        self,
        base_url="",
        auth_token="",
        headers: Optional[dict[str, str]] = None,
        use_async=False,
    ) -> None:
        if auth_token:
            if not headers:
                headers = {}
            headers["Authorization"] = f"Bearer {auth_token}"
        if use_async:
            self.async_client = httpx.AsyncClient(base_url=base_url, headers=headers)
        else:
            self.client = httpx.Client(base_url=base_url, headers=headers)

    def _encode_body(self, data: BaseModel):
        """
        Encode Pydantic data for httpx json body.
        Pydantic model.json() returns a raw string, but httpx expects a stringifiable json.
        """
        return json_lib.loads(data.json())

    def send_request(
        self,
        method: Literal["GET", "POST", "PATCH", "PUT", "DELETE"],
        url: URLTypes,
        *,
        model: Type[T] | None = None,
        content: RequestContent | None = None,
        data: RequestData | None = None,
        files: RequestFiles | None = None,
        json: Any | None = None,
        params: QueryParamTypes | None = None,
        headers: HeaderTypes | None = None,
        cookies: CookieTypes | None = None,
        timeout: TimeoutTypes | UseClientDefault = USE_CLIENT_DEFAULT,
        extensions: RequestExtensions | None = None,
    ) -> APIResponse[T]:
        """
        Simple wrapper around httpx that builds the request, sends it,
        and parses the result.

        https://www.python-httpx.org/advanced/#merging-of-configuration
        - The `params`, `headers` and `cookies` arguments are merged with any values set on the client.
        - The `url` argument is merged with any `base_url` set on the client.

        Args:
                method:
                url:

                --- My custom args ---
                model: The pydantic model to use for parsing the api response, if any.
                        If not provided, response returned is a raw dict.

                --- The remainder of args are the same as for httpx ---
                content:
                data:
                files:
                json:
                params:
                headers:
                cookies:
                timeout:
                extensions:

        Returns:
                The parsed API response.

        """
        # Encode only if we passed in a pydantic model
        # This allows us to also pass plain dicts when needed, which shouldn't be encoded
        if json and isinstance(json, BaseModel):
            json = self._encode_body(json)
        res = self.client.send(
            self.client.build_request(
                method,
                url,
                content=content,
                data=data,
                files=files,
                json=json,
                params=params,
                headers=headers,
                cookies=cookies,
                timeout=timeout,
                extensions=extensions,
            )
        )
        if res.status_code >= 300:
            error_str = res.text
            try:
                error_str = res.json()
            except:
                pass
            raise Exception(error_str)

        # Some apis (e.g. Lunchmoney) return OK status with an error if there is an error
        if "error" in res.json():
            raise Exception(res.json())
        else:
            return (
                APIResponse(response=res, data=model(**res.json()))
                if model
                else APIResponse(response=res, data=res.json())
            )

    def send_request_stream(
        self,
        method: Literal["GET", "POST", "PATCH", "PUT", "DELETE"],
        url: URLTypes,
        *,
        model: Type[T] | None = None,
        content: RequestContent | None = None,
        data: RequestData | None = None,
        files: RequestFiles | None = None,
        json: Any | None = None,
        params: QueryParamTypes | None = None,
        headers: HeaderTypes | None = None,
        cookies: CookieTypes | None = None,
        timeout: TimeoutTypes | UseClientDefault = USE_CLIENT_DEFAULT,
        extensions: RequestExtensions | None = None,
    ) -> Generator[APIResponse[T | None], None, None]:
        """
        Simple wrapper around httpx that builds the request, sends it,
        and parses the result.

        https://www.python-httpx.org/advanced/#merging-of-configuration
        - The `params`, `headers` and `cookies` arguments are merged with any values set on the client.
        - The `url` argument is merged with any `base_url` set on the client.

        Args:
                method:
                url:

                --- My custom args ---
                model: The pydantic model to use for parsing the api response, if any.
                        If not provided, response returned is a raw dict.
                raw_res: Do not parse response chunks (for file downloads, etc)

                --- The remainder of args are the same as for httpx ---
                content:
                data:
                files:
                json:
                params:
                headers:
                cookies:
                timeout:
                extensions:

        Returns:
                The parsed API response.

        """
        # Encode only if we passed in a pydantic model
        # This allows us to also pass plain dicts when needed, which shouldn't be encoded
        if json and isinstance(json, BaseModel):
            json = self._encode_body(json)
        res = self.client.send(
            self.client.build_request(
                method,
                url,
                content=content,
                data=data,
                files=files,
                json=json,
                params=params,
                headers=headers,
                cookies=cookies,
                timeout=timeout,
                extensions=extensions,
            ),
            stream=True,
        )

        if res.status_code >= 300:
            error_str = res.read()
            try:
                error_str = json_lib.loads(res.read())
            except:
                pass
            raise Exception(error_str)

        for chunk in res.iter_text():
            if not chunk or chunk == "data: [DONE]\n\n":
                yield APIResponse(response=res, data=None)
            else:
                # OpenAI API stream returns a non-json string, e.g.:
                # 'data: {"id": "some-id", "model": "gpt-3.5-turbo", ...}'
                # So we need to extract the json portions (may contain multiple data: 's)
                # Unclear if this is an OpenAI API idiosyncracy or common for streams
                # but this should work the same if it was a valid json string anyway
                json_matches: list[str] = re.findall(r"\{.*\}", chunk)
                if not len(json_matches):
                    raise Exception(f"Invalid chunk format (JSON not found): ", chunk)
                for match in json_matches:
                    yield APIResponse(
                        response=res,
                        data=model(**json_lib.loads(match))
                        if model
                        else json_lib.loads(match),
                    )

    def send_request_stream_raw(
        self,
        method: Literal["GET", "POST", "PATCH", "PUT", "DELETE"],
        url: URLTypes,
        *,
        content: RequestContent | None = None,
        data: RequestData | None = None,
        files: RequestFiles | None = None,
        json: Any | None = None,
        params: QueryParamTypes | None = None,
        headers: HeaderTypes | None = None,
        cookies: CookieTypes | None = None,
        timeout: TimeoutTypes | UseClientDefault = USE_CLIENT_DEFAULT,
        extensions: RequestExtensions | None = None,
    ):
        """
        Simple wrapper around httpx that builds the request, sends it,
        and passes back an iterator over the raw result (for e.g. file downloads).

        https://www.python-httpx.org/advanced/#merging-of-configuration
        - The `params`, `headers` and `cookies` arguments are merged with any values set on the client.
        - The `url` argument is merged with any `base_url` set on the client.

        Args:
                method:
                url:

                --- My custom args ---
                model: The pydantic model to use for parsing the api response, if any.
                        If not provided, response returned is a raw dict.
                raw_res: Do not parse response chunks (for file downloads, etc)

                --- The remainder of args are the same as for httpx ---
                content:
                data:
                files:
                json:
                params:
                headers:
                cookies:
                timeout:
                extensions:

        Returns:
                The parsed API response.

        """
        # Encode only if we passed in a pydantic model
        # This allows us to also pass plain dicts when needed, which shouldn't be encoded
        if json and isinstance(json, BaseModel):
            json = self._encode_body(json)
        res = self.client.send(
            self.client.build_request(
                method,
                url,
                content=content,
                data=data,
                files=files,
                json=json,
                params=params,
                headers=headers,
                cookies=cookies,
                timeout=timeout,
                extensions=extensions,
            ),
            stream=True,
        )

        if res.status_code >= 300:
            error_str = res.read()
            try:
                error_str = json_lib.loads(res.read())
            except:
                pass
            raise Exception(error_str)

        for chunk in res.iter_bytes():
            yield chunk

    async def send_request_async(
        self,
        method: Literal["GET", "POST", "PATCH", "PUT", "DELETE"],
        url: URLTypes,
        *,
        model: Type[T] | None = None,
        content: RequestContent | None = None,
        data: RequestData | None = None,
        files: RequestFiles | None = None,
        json: Any | None = None,
        params: QueryParamTypes | None = None,
        headers: HeaderTypes | None = None,
        cookies: CookieTypes | None = None,
        timeout: TimeoutTypes | UseClientDefault = USE_CLIENT_DEFAULT,
        extensions: RequestExtensions | None = None,
    ) -> APIResponse[T]:
        """
        Simple wrapper around httpx that builds the request, sends it,
        and parses the result.

        https://www.python-httpx.org/advanced/#merging-of-configuration
        - The `params`, `headers` and `cookies` arguments are merged with any values set on the client.
        - The `url` argument is merged with any `base_url` set on the client.

        Args:
                method:
                url:

                --- My custom args ---
                model: The pydantic model to use for parsing the api response, if any.
                        If not provided, response returned is a raw dict.

                --- The remainder of args are the same as for httpx ---
                content:
                data:
                files:
                json:
                params:
                headers:
                cookies:
                timeout:
                extensions:

        Returns:
                The parsed API response.

        """
        # Encode only if we passed in a pydantic model
        # This allows us to also pass plain dicts when needed, which shouldn't be encoded
        if json and isinstance(json, BaseModel):
            json = self._encode_body(json)
        res = await self.async_client.send(
            self.async_client.build_request(
                method,
                url,
                content=content,
                data=data,
                files=files,
                json=json,
                params=params,
                headers=headers,
                cookies=cookies,
                timeout=timeout,
                extensions=extensions,
            )
        )
        if res.status_code >= 300:
            error_str = res.text
            try:
                error_str = res.json()
            except:
                pass
            raise Exception(error_str)

        # Some apis (e.g. Lunchmoney) return OK status with an error if there is an error
        if "error" in res.json():
            raise Exception(res.json())
        else:
            return (
                APIResponse(response=res, data=model(**res.json()))
                if model
                else res.json()
            )

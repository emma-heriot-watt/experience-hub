from collections.abc import Generator

import httpx
from pydantic import AnyHttpUrl
from pytest_cases import fixture
from pytest_httpx import HTTPXMock

from emma_experience_hub.api.clients import ProfanityFilterClient


@fixture(scope="session")
def profanity_filter_client(httpx_mock: HTTPXMock) -> Generator[ProfanityFilterClient, None, None]:
    def custom_response(request: httpx.Request) -> httpx.Response:  # noqa: WPS430
        text = request.content.decode("utf-8")
        # If request contains the word "profanity" anywhere, return True
        return httpx.Response(status_code=200, json="profanity" in text)

    httpx_mock.add_callback(custom_response)
    yield ProfanityFilterClient(endpoint=AnyHttpUrl(url="http://localhost", scheme="http"))

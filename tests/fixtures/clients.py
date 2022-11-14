from collections.abc import Generator

import httpx
from pydantic import AnyHttpUrl
from pytest_cases import fixture
from pytest_httpx import HTTPXMock

from emma_experience_hub.api.clients import ProfanityFilterClient
from emma_experience_hub.api.clients.simbot import SimBotUtteranceGeneratorClient


@fixture(scope="session")
def profanity_filter_client(httpx_mock: HTTPXMock) -> Generator[ProfanityFilterClient, None, None]:
    def custom_response(request: httpx.Request) -> httpx.Response:  # noqa: WPS430
        text = request.content.decode("utf-8")
        # If request contains the word "profanity" anywhere, return True
        return httpx.Response(status_code=200, json="profanity" in text)

    httpx_mock.add_callback(custom_response)
    yield ProfanityFilterClient(endpoint=AnyHttpUrl(url="http://localhost", scheme="http"))


@fixture
def utterance_generator_client(
    httpx_mock: HTTPXMock,
) -> Generator[SimBotUtteranceGeneratorClient, None, None]:
    def custom_response(request: httpx.Request) -> httpx.Response:  # noqa: WPS430
        return httpx.Response(status_code=200, json="utterance_go_here")

    httpx_mock.add_callback(custom_response)
    assert httpx.post("http://localhost").json() == "utterance_go_here"
    yield SimBotUtteranceGeneratorClient(
        endpoint=AnyHttpUrl(url="http://localhost", scheme="http")
    )

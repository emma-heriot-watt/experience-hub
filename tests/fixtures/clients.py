from collections.abc import Generator

import httpx
from pydantic import AnyHttpUrl
from pytest_cases import fixture
from pytest_httpx import HTTPXMock

from emma_experience_hub.api.clients import UtteranceGeneratorClient
from emma_experience_hub.api.clients.simbot import SimBotSessionDbClient


@fixture
def dynamo_db_client() -> SimBotSessionDbClient:
    return SimBotSessionDbClient("us-east-1", "MEMORY_TABLE_test")


@fixture
def utterance_generator_client(
    httpx_mock: HTTPXMock,
) -> Generator[UtteranceGeneratorClient, None, None]:
    def custom_response(request: httpx.Request) -> httpx.Response:  # noqa: WPS430
        return httpx.Response(status_code=200, json="utterance_go_here")

    httpx_mock.add_callback(custom_response)
    assert httpx.post("http://localhost").json() == "utterance_go_here"
    yield UtteranceGeneratorClient(endpoint=AnyHttpUrl(url="http://localhost", scheme="http"))

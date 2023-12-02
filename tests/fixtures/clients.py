from collections.abc import Generator

import httpx
from pydantic import AnyHttpUrl
from pytest import MonkeyPatch, fixture
from pytest_httpx import HTTPXMock

from emma_experience_hub.api.clients import ProfanityFilterClient
from emma_experience_hub.api.clients.simbot import (
    SimbotActionPredictionClient,
    SimBotFeaturesClient,
    SimBotNLUIntentClient,
)
from emma_experience_hub.datamodels import EmmaExtractedFeatures
from tests.fixtures.simbot_arena_constants import create_placeholder_features_frames


@fixture(scope="session")
def profanity_filter_client(httpx_mock: HTTPXMock) -> Generator[ProfanityFilterClient, None, None]:
    def custom_response(request: httpx.Request) -> httpx.Response:  # noqa: WPS430
        text = request.content.decode("utf-8")
        # If request contains the word "profanity" anywhere, return True
        return httpx.Response(status_code=200, json="profanity" in text)

    httpx_mock.add_callback(custom_response)
    yield ProfanityFilterClient(
        endpoint=AnyHttpUrl(url="http://localhost", scheme="http"), timeout=None
    )


@fixture
def mock_feature_extraction_response(monkeypatch: MonkeyPatch) -> None:
    """Mock get_features from the SimBotFeaturesClient."""

    def mock_get_features(*args, **kwargs) -> list[EmmaExtractedFeatures]:  # noqa: WPS430
        features = create_placeholder_features_frames()
        return features

    monkeypatch.setattr(SimBotFeaturesClient, "get_features", mock_get_features)


@fixture
def mock_policy_response_goto_room(monkeypatch: MonkeyPatch) -> None:
    """Mock the responses of EMMA policy."""

    def get_nlu(*args, **kwargs) -> str:  # noqa: WPS430
        return "<act><one_match>"

    def get_action(*args, **kwargs) -> str:  # noqa: WPS430
        return "goto breakroom<stop>."

    monkeypatch.setattr(SimBotNLUIntentClient, "generate", get_nlu)
    monkeypatch.setattr(SimbotActionPredictionClient, "generate", get_action)


@fixture
def mock_policy_response_toggle_computer(monkeypatch: MonkeyPatch) -> None:
    """Mock the responses of EMMA policy when the input instruction is about turning on the
    computer."""

    def get_nlu(*args, **kwargs) -> str:  # noqa: WPS430
        return "<act><one_match>"

    def get_action(*args, **kwargs) -> str:  # noqa: WPS430
        return "toggle computer <frame_token_1> <vis_token_1><stop>."

    monkeypatch.setattr(SimBotNLUIntentClient, "generate", get_nlu)
    monkeypatch.setattr(SimbotActionPredictionClient, "generate", get_action)


@fixture
def mock_policy_response_search(monkeypatch: MonkeyPatch) -> None:
    """Mock the responses of EMMA policy when the input instruction is about searching an
    object."""

    def get_nlu(*args, **kwargs) -> str:  # noqa: WPS430
        return "<search>"

    def get_object(*args, **kwargs) -> list[str]:  # noqa: WPS430
        return ["<frame_token_1> <vis_token_1>"]

    def get_target(*args, **kwargs) -> str:  # noqa: WPS430
        return "goto object <frame_token_1> <vis_token_1> <stop>."

    monkeypatch.setattr(SimBotNLUIntentClient, "generate", get_nlu)
    monkeypatch.setattr(SimbotActionPredictionClient, "find_object_in_scene", get_object)
    monkeypatch.setattr(SimbotActionPredictionClient, "generate", get_target)

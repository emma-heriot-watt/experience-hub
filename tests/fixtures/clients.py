from typing import Any

from pytest import MonkeyPatch, fixture

from emma_experience_hub.api.clients.simbot import (
    SimbotActionPredictionClient,
    SimBotCRIntentClient,
    SimBotFeaturesClient,
)
from emma_experience_hub.datamodels import EmmaExtractedFeatures
from tests.fixtures.simbot_arena_constants import create_placeholder_features_frames


@fixture
def mock_feature_extraction_response(monkeypatch: MonkeyPatch) -> None:
    """Mock get_features from the SimBotFeaturesClient."""

    def mock_features(*args: Any, **kwargs: Any) -> list[EmmaExtractedFeatures]:  # noqa: WPS430
        features = create_placeholder_features_frames()
        return features

    monkeypatch.setattr(SimBotFeaturesClient, "get_features", mock_features)


@fixture
def mock_policy_response_goto_room(monkeypatch: MonkeyPatch) -> None:
    """Mock the responses of EMMA policy."""

    def get_cr(*args: Any, **kwargs: Any) -> str:  # noqa: WPS430
        return "<act><one_match>"

    def get_action(*args: Any, **kwargs: Any) -> str:  # noqa: WPS430
        return "goto breakroom<stop>."

    monkeypatch.setattr(SimBotCRIntentClient, "generate", get_cr)
    monkeypatch.setattr(SimbotActionPredictionClient, "generate", get_action)


@fixture
def mock_policy_response_toggle_computer(monkeypatch: MonkeyPatch) -> None:
    """Mock the responses of EMMA policy when the input instruction is about turning on the
    computer."""

    def get_cr(*args: Any, **kwargs: Any) -> str:  # noqa: WPS430
        return "<act><one_match>"

    def get_action(*args: Any, **kwargs: Any) -> str:  # noqa: WPS430
        return "toggle computer <frame_token_1> <vis_token_1><stop>."

    monkeypatch.setattr(SimBotCRIntentClient, "generate", get_cr)
    monkeypatch.setattr(SimbotActionPredictionClient, "generate", get_action)


@fixture
def mock_policy_response_search(monkeypatch: MonkeyPatch) -> None:
    """Mock the responses of EMMA policy when the input instruction is about searching an
    object."""

    def get_cr(*args: Any, **kwargs: Any) -> str:  # noqa: WPS430
        return "<search>"

    def get_object(*args: Any, **kwargs: Any) -> list[str]:  # noqa: WPS430
        return ["<frame_token_1> <vis_token_1>"]

    def get_target(*args: Any, **kwargs: Any) -> str:  # noqa: WPS430
        return "goto object <frame_token_1> <vis_token_1> <stop>."

    monkeypatch.setattr(SimBotCRIntentClient, "generate", get_cr)
    monkeypatch.setattr(SimbotActionPredictionClient, "find_object_in_scene", get_object)
    monkeypatch.setattr(SimbotActionPredictionClient, "generate", get_target)

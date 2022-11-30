from typing import Optional

import pytest
from hypothesis import assume, given, settings, strategies as st
from pytest_cases import fixture, parametrize

from emma_experience_hub.constants.model import MODEL_EOS_TOKEN, PREDICTED_ACTION_DELIMITER
from emma_experience_hub.constants.simbot import (
    ACTION_SYNONYMS,
    get_simbot_object_label_to_class_name_map,
    get_simbot_room_name_map,
)
from emma_experience_hub.datamodels.emma import EmmaExtractedFeatures
from emma_experience_hub.datamodels.simbot import SimBotAction, SimBotActionType
from emma_experience_hub.datamodels.simbot.payloads import (
    SimBotGotoObjectPayload,
    SimBotGotoPayload,
    SimBotGotoRoomPayload,
    SimBotInteractionObject,
    SimBotObjectInteractionPayload,
    SimBotTurnAroundPayload,
)
from emma_experience_hub.functions.simbot import (
    get_correct_frame_index,
    get_mask_from_special_tokens,
)
from emma_experience_hub.parsers.simbot import SimBotActionPredictorOutputParser
from tests.fixtures.simbot_actions import simbot_extracted_features, simbot_room_names


@given(data=st.data(), frame_token_id=st.integers(1, 2), visual_token_id=st.integers(1, 2))
@settings(deadline=None, max_examples=5)
def test_can_get_correct_mask_from_special_tokens(
    data: st.DataObject,
    frame_token_id: int,
    visual_token_id: int,
) -> None:
    """Tests that the parser uses the correct visual token when creating the object mask."""
    extracted_features: list[EmmaExtractedFeatures] = data.draw(
        simbot_extracted_features(
            num_frames=st.just(frame_token_id), min_num_objects=st.just(visual_token_id)
        )
    )

    _, candidate_coords = get_mask_from_special_tokens(
        frame_token_id, visual_token_id, extracted_features, return_coords=True
    )

    bbox_coords = tuple(
        extracted_features[frame_token_id - 1].bbox_coords[visual_token_id - 1].tolist()
    )
    assert candidate_coords == bbox_coords


@parametrize(
    "predicted_frame, current_frames, total_frames, expected_frame",
    [
        (1, 4, 5, 0),  # error case: predicted frame should be in [2,5]
        (2, 4, 5, 0),  # get the the 1st of the latest 4 frames
        (3, 4, 5, 1),  # get the the 2nd of the latest 4 frames
        (4, 4, 5, 2),  # get the the 3rd of the latest 4 frames
        (5, 4, 5, 3),  # get the the 4th of the latest 4 frames
        (5, 1, 5, 0),  # one current frame with total 5 frames, correct prediction (5)
        (4, 1, 5, 0),  # one current frame with total 5 frames, incorrect prediction (4)
    ],
)
def test_can_get_correct_frame_index(
    predicted_frame: int,
    current_frames: int,
    total_frames: int,
    expected_frame: int,
) -> None:
    """Test that the parser returns a valid frame index."""
    predicted_frame = get_correct_frame_index(predicted_frame, current_frames, total_frames)

    # Verify the parsed frame is correct
    assert predicted_frame == expected_frame


@fixture(scope="module")
def simbot_action_parser() -> SimBotActionPredictorOutputParser:
    return SimBotActionPredictorOutputParser(PREDICTED_ACTION_DELIMITER, MODEL_EOS_TOKEN)


@st.composite
def raw_decoded_outputs(
    draw: st.DrawFn,
    action: st.SearchStrategy[str],
    entity: st.SearchStrategy[str],
    include_end_of_trajectory: st.SearchStrategy[bool] = st.booleans(),
    frame_token_id: st.SearchStrategy[Optional[int]] = st.one_of(st.none(), st.integers(1, 4)),
    visual_token_id: st.SearchStrategy[Optional[int]] = st.one_of(st.none(), st.integers(1, 4)),
) -> str:
    """Generate raw decoded output trajectories."""
    raw_output = f"{draw(action)} {draw(entity)}"

    drawn_frame_token_id = draw(frame_token_id)
    if drawn_frame_token_id is not None:
        raw_output = f"{raw_output} <frame_token_{drawn_frame_token_id}>"

    drawn_visual_token_id = draw(visual_token_id)
    if drawn_visual_token_id is not None:
        raw_output = f"{raw_output} <vis_token_{drawn_visual_token_id}>"

    if draw(include_end_of_trajectory):
        raw_output = f"{raw_output} <stop>"

    raw_output = f"{raw_output}.</s>".lower()
    return raw_output


def _get_expected_color_image_index(entity: str, frame_token_id: Optional[int] = None) -> int:
    if "sticky" in entity.lower() or frame_token_id is None:
        return 0

    return frame_token_id - 1


@given(
    data=st.data(),
    room_name=simbot_room_names(),
    simbot_extracted_features=simbot_extracted_features(),
)
def test_simbot_action_parser_room_navigation(
    data: st.DataObject,
    room_name: str,
    simbot_extracted_features: list[EmmaExtractedFeatures],
    simbot_action_parser: SimBotActionPredictorOutputParser,
) -> None:
    """Tests that the parser returns room navigation actions."""
    raw_output = data.draw(
        raw_decoded_outputs(
            action=st.just("goto"),
            entity=st.just(room_name),
            frame_token_id=st.none(),
            visual_token_id=st.none(),
        )
    )

    expected_action = SimBotAction(
        id=0,
        type=SimBotActionType.Goto,
        raw_output=raw_output.removesuffix("</s>").removesuffix("."),
        payload=SimBotGotoPayload(
            object=SimBotGotoRoomPayload(officeRoom=get_simbot_room_name_map()[room_name.lower()]),
        ),
    )

    parsed_action = simbot_action_parser(
        raw_output,
        extracted_features=simbot_extracted_features,
        num_frames_in_current_turn=len(simbot_extracted_features),
    )
    assert parsed_action == expected_action


def _build_raw_output(
    action: str,
    entity: str,
    include_end_of_trajectory: bool,
    visual_token_id: Optional[int] = None,
    frame_token_id: Optional[int] = None,
) -> str:
    """Build the raw output.

    This is done repeatedly by all the tests, so lets just abstract it.
    """
    raw_output = f"{action} {entity}"

    if frame_token_id is not None:
        raw_output = f"{raw_output} <frame_token_{frame_token_id}>"

    if visual_token_id is not None:
        raw_output = f"{raw_output} <vis_token_{visual_token_id}>"

    if include_end_of_trajectory:
        raw_output = f"{raw_output} <stop>"

    raw_output = f"{raw_output}.</s>".lower()

    return raw_output


@given(
    include_end_of_trajectory=st.booleans(),
    frame_token_id=st.one_of(st.none(), st.integers(1, 2)),
    visual_token_id=st.one_of(st.none(), st.integers(1, 2)),
)
@settings(deadline=None, max_examples=5)
def test_simbot_action_parser_object_navigation(
    simbot_object_name: str,
    include_end_of_trajectory: bool,
    simbot_action_parser: SimBotActionPredictorOutputParser,
    frame_token_id: Optional[int],
    visual_token_id: Optional[int],
    simbot_extracted_features: list[EmmaExtractedFeatures],
) -> None:
    """Tests that the parser returns correct object navigation actions."""
    assume(visual_token_id is not None and frame_token_id is not None)

    raw_output = _build_raw_output(
        "goto",
        simbot_object_name,
        visual_token_id=visual_token_id,
        frame_token_id=frame_token_id,
        include_end_of_trajectory=include_end_of_trajectory,
    )
    expected_action = SimBotAction(
        id=0,
        type=SimBotActionType.Goto,
        payload=SimBotGotoPayload(
            object=SimBotGotoObjectPayload(
                name=get_simbot_object_label_to_class_name_map()[simbot_object_name],
                colorImageIndex=_get_expected_color_image_index(
                    simbot_object_name, frame_token_id
                ),
                mask=None,
            ),
        ),
    )

    parsed_action = simbot_action_parser(
        raw_output,
        extracted_features=simbot_extracted_features,
        num_frames_in_current_turn=len(simbot_extracted_features),
    )

    # Check if everything is identical except the compressed mask
    assert parsed_action.type == expected_action.type

    assert isinstance(parsed_action.payload, SimBotGotoPayload)
    assert isinstance(expected_action.payload, SimBotGotoPayload)

    assert isinstance(parsed_action.payload.object, SimBotGotoObjectPayload)
    assert isinstance(expected_action.payload.object, SimBotGotoObjectPayload)

    assert (
        parsed_action.payload.object.color_image_index
        == expected_action.payload.object.color_image_index
    )
    assert parsed_action.payload.object.name == expected_action.payload.object.name

    parsed_action_type_payload = getattr(parsed_action, parsed_action.type.name.lower())
    expected_action_type_payload = getattr(expected_action, expected_action.type.name.lower())
    assert (
        parsed_action_type_payload.object.color_image_index
        == expected_action_type_payload.object.color_image_index
    )
    assert parsed_action_type_payload.object.name == expected_action_type_payload.object.name


@given(
    include_end_of_trajectory=st.booleans(),
    frame_token_id=st.integers(1, 2),
    visual_token_id=st.integers(1, 2),
)
@settings(deadline=None, max_examples=2)
def test_simbot_action_parser_object_interaction(
    simbot_interaction_action: str,
    simbot_object_name: str,
    include_end_of_trajectory: bool,
    simbot_action_parser: SimBotActionPredictorOutputParser,
    frame_token_id: Optional[int],
    visual_token_id: Optional[int],
    simbot_extracted_features: list[EmmaExtractedFeatures],
) -> None:
    """Tests that the parser returns correct object interaction actions actions."""
    if visual_token_id is None or frame_token_id is None:
        pytest.skip(
            "We are no longer attempting to parse object-related actions when no visual token is present. Stop the test here."
        )

    raw_output = _build_raw_output(
        simbot_interaction_action,
        simbot_object_name,
        visual_token_id=visual_token_id,
        frame_token_id=frame_token_id,
        include_end_of_trajectory=include_end_of_trajectory,
    )

    parsed_action = simbot_action_parser(
        raw_output,
        extracted_features=simbot_extracted_features,
        num_frames_in_current_turn=len(simbot_extracted_features),
    )

    try:
        expected_object_name = get_simbot_object_label_to_class_name_map()[simbot_object_name]
    except KeyError:
        expected_object_name = simbot_object_name

    expected_action = SimBotAction(
        id=0,
        type=SimBotActionType[simbot_interaction_action],
        raw_output=raw_output.removesuffix("</s>").removesuffix("."),
        payload=SimBotObjectInteractionPayload(
            object=SimBotInteractionObject(
                name=expected_object_name,
                colorImageIndex=_get_expected_color_image_index(
                    simbot_object_name, frame_token_id
                ),
                mask=None,
            )
        ),
    )

    # Check if everything is identical except the compressed mask
    assert parsed_action.type == expected_action.type

    assert isinstance(parsed_action.payload, SimBotObjectInteractionPayload)
    assert isinstance(expected_action.payload, SimBotObjectInteractionPayload)

    assert isinstance(parsed_action.payload.object, SimBotInteractionObject)
    assert isinstance(expected_action.payload.object, SimBotInteractionObject)

    assert (
        parsed_action.payload.object.color_image_index
        == expected_action.payload.object.color_image_index
    )
    assert parsed_action.payload.object.name == expected_action.payload.object.name

    parsed_action_type_payload = getattr(parsed_action, parsed_action.type.name.lower())
    expected_action_type_payload = getattr(expected_action, expected_action.type.name.lower())
    assert (
        parsed_action_type_payload.object.color_image_index
        == expected_action_type_payload.object.color_image_index
    )
    assert parsed_action_type_payload.object.name == expected_action_type_payload.object.name


@parametrize(
    "low_level_navigation_trajectory, low_level_navigation_action",
    sorted(
        (trajectory, action)
        for action, trajectory_set in ACTION_SYNONYMS.items()
        for trajectory in trajectory_set
        if action in SimBotActionType.low_level_navigation()
    ),
)
def test_simbot_action_parser_low_level_action(
    low_level_navigation_trajectory: str,
    low_level_navigation_action: SimBotActionType,
    simbot_action_parser: SimBotActionPredictorOutputParser,
    simbot_extracted_features: list[EmmaExtractedFeatures],
) -> None:
    """Tests that the parser returns correct low level actions."""
    raw_output = f"{low_level_navigation_trajectory} <stop>.</s>"
    expected_action = SimBotAction(
        id=0,
        type=low_level_navigation_action.base_type,
        payload=low_level_navigation_action.payload_model(),
        raw_output=raw_output.removesuffix("</s>").removesuffix("."),
    )

    parsed_action = simbot_action_parser(
        raw_output,
        extracted_features=simbot_extracted_features,
        num_frames_in_current_turn=len(simbot_extracted_features),
    )
    assert parsed_action == expected_action


@parametrize(
    "raw_output",
    [
        "examine sticky note <stop>.</s>",
        "examine sticky note <frame_token_1> <stop>.</s>",
        "examine sticky note <frame_token_1> <vis_token_5> <stop>.</s>",
    ],
)
def test_simbot_action_parser_sticky_note(
    raw_output: str,
    simbot_action_parser: SimBotActionPredictorOutputParser,
    simbot_extracted_features: list[EmmaExtractedFeatures],
) -> None:
    """Tests that the parser returns correct low level actions."""
    expected_action = SimBotAction(
        id=0,
        type=SimBotActionType.Examine,
        payload=SimBotObjectInteractionPayload(
            object=SimBotInteractionObject(colorImageIndex=0, mask=None, name="stickynote")
        ),
        status=None,
        raw_output=raw_output.removesuffix("</s>").removesuffix("."),
    )

    parsed_action = simbot_action_parser(
        raw_output,
        extracted_features=simbot_extracted_features,
        num_frames_in_current_turn=len(simbot_extracted_features),
    )
    assert parsed_action == expected_action


@parametrize(
    "raw_output",
    ["turn around <stop>.</s>", "turn around."],
)
def test_simbot_turn_around_action(
    raw_output: str,
    simbot_action_parser: SimBotActionPredictorOutputParser,
    simbot_extracted_features: list[EmmaExtractedFeatures],
) -> None:
    """Tests that the parser returns correct low level actions."""
    expected_action = SimBotAction(
        id=0,
        type=SimBotActionType.Rotate,
        status=None,
        payload=SimBotTurnAroundPayload(),
        raw_output=raw_output.removesuffix("</s>").removesuffix("."),
    )

    parsed_action = simbot_action_parser(
        raw_output,
        extracted_features=simbot_extracted_features,
        num_frames_in_current_turn=len(simbot_extracted_features),
    )
    assert parsed_action == expected_action

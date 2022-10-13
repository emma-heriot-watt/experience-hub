from typing import Optional

from pytest_cases import param_fixture, parametrize, parametrize_with_cases

from emma_experience_hub.api.clients import UtteranceGeneratorClient
from emma_experience_hub.constants.model import (
    END_OF_TRAJECTORY_TOKEN,
    MODEL_EOS_TOKEN,
    PREDICTED_ACTION_DELIMITER,
)
from emma_experience_hub.constants.simbot import (
    ACTION_SYNONYMS,
    get_simbot_object_label_to_class_name_map,
    get_simbot_room_name_map,
)
from emma_experience_hub.datamodels.simbot import SimBotAction, SimBotActionType
from emma_experience_hub.datamodels.simbot.payloads import (
    SimBotGotoObjectPayload,
    SimBotGotoPayload,
    SimBotGotoRoomPayload,
    SimBotInteractionObject,
    SimBotObjectInteractionPayload,
)
from emma_experience_hub.parsers.simbot import SimBotActionPredictorOutputParser


frame_token_id = param_fixture(
    "frame_token_id",
    [None, 0, 2],
    ids=["any_frame", "in_frame_0", "in_frame_2"],
    scope="module",
)

visual_token_id = param_fixture(
    "visual_token_id",
    [None, 5, 12],
    ids=["no_visual_token", "<vis_token_5>", "<vis_token_12>"],
    scope="module",
)


class DecodedSimBotTrajectories:
    def case_goto_room(self, simbot_room_name: str) -> tuple[str, SimBotAction]:
        trajectory = f"Goto {simbot_room_name}"
        action = SimBotAction(
            type=SimBotActionType.Goto,
            payload=SimBotGotoPayload(
                object=SimBotGotoRoomPayload(
                    officeRoom=get_simbot_room_name_map()[simbot_room_name.lower()]
                ),
            ),
        )
        return trajectory.lower(), action

    def case_with_wrong_actions(
        self, frame_token_id: Optional[int], visual_token_id: Optional[int]
    ) -> tuple[str, SimBotAction]:
        """Be able to parse the wrong actions best as possible.

        Inspired by `cleanoggle sink <frame_token_1>. clean sink <frame_token_2>`.
        """
        incorrect_action = "cleanoggle sink"
        correct_action = "clean sink"

        if frame_token_id is not None:
            incorrect_action = f"{incorrect_action} <frame_token_{frame_token_id+1}>"
            correct_action = f"{correct_action} <frame_token_{frame_token_id+1}>"

        if visual_token_id is not None:
            incorrect_action = f"{incorrect_action} <vis_token_{visual_token_id}>"
            correct_action = f"{correct_action} <vis_token_{visual_token_id}>"

        trajectory = f"{incorrect_action}. {correct_action}."

        action = SimBotAction(
            type=SimBotActionType.Clean,
            payload=SimBotObjectInteractionPayload(
                object=SimBotInteractionObject(
                    name="sink",
                    colorImageIndex=0,  # image index is 0 if no features are provided
                    mask=None,
                )
            ),
        )

        return trajectory.lower(), action

    def case_goto_object(
        self,
        simbot_object_name: str,
        frame_token_id: Optional[int],
        visual_token_id: Optional[int],
    ) -> tuple[str, SimBotAction]:
        trajectory = f"Goto {simbot_object_name.lower()}"

        if frame_token_id is not None:
            trajectory = f"{trajectory} <frame_token_{frame_token_id+1}>"

        if visual_token_id is not None:
            trajectory = f"{trajectory} <vis_token_{visual_token_id}>"

        action = SimBotAction(
            type=SimBotActionType.Goto,
            payload=SimBotGotoPayload(
                object=SimBotGotoObjectPayload(
                    name=get_simbot_object_label_to_class_name_map()[simbot_object_name],
                    colorImageIndex=0,  # image index is 0 if no features are provided
                    mask=None,
                ),
            ),
        )
        return trajectory.lower(), action

    def case_object_interaction(
        self,
        simbot_interaction_action: str,
        simbot_object_name: str,
        frame_token_id: Optional[int],
        visual_token_id: Optional[int],
    ) -> tuple[str, SimBotAction]:
        trajectory = f"{simbot_interaction_action} {simbot_object_name}"

        if frame_token_id is not None:
            trajectory = f"{trajectory} <frame_token_{frame_token_id+1}>"

        if visual_token_id is not None:
            trajectory = f"{trajectory} <vis_token_{visual_token_id}>"

        action = SimBotAction(
            type=SimBotActionType[simbot_interaction_action],
            payload=SimBotObjectInteractionPayload(
                object=SimBotInteractionObject(
                    name=get_simbot_object_label_to_class_name_map()[simbot_object_name],
                    colorImageIndex=0,  # image index is 0 if no features are provided
                    mask=None,
                )
            ),
        )

        return trajectory.lower(), action

    @parametrize(
        "low_level_navigation_trajectory, low_level_navigation_action",
        sorted(
            (trajectory, action)
            for action, trajectory_set in ACTION_SYNONYMS.items()
            for trajectory in trajectory_set
            if action in SimBotActionType.low_level_navigation()
        ),
    )
    def case_low_level_navigation(
        self, low_level_navigation_trajectory: str, low_level_navigation_action: SimBotActionType
    ) -> tuple[str, SimBotAction]:
        action = SimBotAction(
            type=low_level_navigation_action.base_type,
            payload=low_level_navigation_action.payload_model(),
        )

        return low_level_navigation_trajectory.lower(), action


@parametrize(
    "include_end_of_trajectory",
    [True, False],
    ids=["with_end_of_trajectory", "without_end_of_trajectory"],
)
@parametrize_with_cases("raw_output,expected_action", cases=DecodedSimBotTrajectories)
def test_simbot_decoded_actions_are_parsed_correctly(
    raw_output: str,
    expected_action: SimBotAction,
    include_end_of_trajectory: bool,
    utterance_generator_client: UtteranceGeneratorClient,
) -> None:
    # Include the end of trajectory token if desired
    if include_end_of_trajectory:
        raw_output = f"{raw_output} {END_OF_TRAJECTORY_TOKEN}"

    # Make sure action delimiter is on the end
    if not raw_output.endswith(PREDICTED_ACTION_DELIMITER):
        raw_output += PREDICTED_ACTION_DELIMITER

    # Add the EOS token
    raw_output += MODEL_EOS_TOKEN

    raw_output = raw_output.lower()

    action_parser = SimBotActionPredictorOutputParser(
        PREDICTED_ACTION_DELIMITER, MODEL_EOS_TOKEN, utterance_generator_client
    )
    parsed_action = action_parser(raw_output)

    # Verify the parsed action is correct
    assert parsed_action == expected_action


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
def test_simbot_frame_token_prediction(
    predicted_frame: int,
    current_frames: int,
    total_frames: int,
    expected_frame: int,
    utterance_generator_client: UtteranceGeneratorClient,
) -> None:
    """Test that the parser returns a valid frame index."""
    action_parser = SimBotActionPredictorOutputParser(
        PREDICTED_ACTION_DELIMITER, MODEL_EOS_TOKEN, utterance_generator_client
    )
    predicted_frame = action_parser._get_correct_frame_index(
        predicted_frame, current_frames, total_frames
    )

    # Verify the parsed frame is correct
    assert predicted_frame == expected_frame

from typing import Optional

from pytest_cases import param_fixture, parametrize, parametrize_with_cases

from emma_experience_hub.api.clients import UtteranceGeneratorClient
from emma_experience_hub.constants.model import MODEL_EOS_TOKEN, PREDICTED_ACTION_DELIMITER
from emma_experience_hub.constants.simbot import (
    ACTION_SYNONYMS,
    load_simbot_object_label_to_class_name_map,
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
                object=SimBotGotoRoomPayload(officeRoom=simbot_room_name),
            ),
        )
        return trajectory, action

    def case_goto_object(
        self,
        simbot_object_name: str,
        frame_token_id: Optional[int],
        visual_token_id: Optional[int],
    ) -> tuple[str, SimBotAction]:
        trajectory = f"Goto {simbot_object_name}"
        simbot_object_classname = load_simbot_object_label_to_class_name_map()[simbot_object_name]

        if frame_token_id:
            trajectory = f"{trajectory} <frame_token_{frame_token_id}>"

        if visual_token_id:
            trajectory = f"{trajectory} <vis_token_{visual_token_id}>"

        action = SimBotAction(
            type=SimBotActionType.Goto,
            payload=SimBotGotoPayload(
                object=SimBotGotoObjectPayload(
                    name=simbot_object_classname,
                    colorImageIndex=frame_token_id if frame_token_id else 0,
                    mask=None,
                ),
            ),
        )
        return trajectory, action

    def case_object_interaction(
        self,
        simbot_interaction_action: str,
        simbot_object_name: str,
        frame_token_id: Optional[int],
        visual_token_id: Optional[int],
    ) -> tuple[str, SimBotAction]:
        trajectory = f"{simbot_interaction_action} {simbot_object_name}"
        simbot_object_classname = load_simbot_object_label_to_class_name_map()[simbot_object_name]

        if frame_token_id:
            trajectory = f"{trajectory} <frame_token_{frame_token_id}>"

        if visual_token_id:
            trajectory = f"{trajectory} <vis_token_{visual_token_id}>"

        action = SimBotAction(
            type=SimBotActionType[simbot_interaction_action],
            payload=SimBotObjectInteractionPayload(
                object=SimBotInteractionObject(
                    name=simbot_object_classname,
                    colorImageIndex=frame_token_id if frame_token_id else 0,
                    mask=None,
                )
            ),
        )

        return trajectory, action

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

        return low_level_navigation_trajectory, action


@parametrize("include_eos", [True, False], ids=["with_eos", "without_eos"])
@parametrize_with_cases("raw_output,expected_action", cases=DecodedSimBotTrajectories)
def test_simbot_decoded_actions_are_parsed_correctly(
    raw_output: str,
    expected_action: SimBotAction,
    include_eos: bool,
    utterance_generator_client: UtteranceGeneratorClient,
) -> None:
    # Make sure action delimiter is on the end
    if not raw_output.endswith(PREDICTED_ACTION_DELIMITER):
        raw_output += PREDICTED_ACTION_DELIMITER

    # If EOS is desired, include it on the end of the actions
    if include_eos:
        raw_output += MODEL_EOS_TOKEN

    action_parser = SimBotActionPredictorOutputParser(
        PREDICTED_ACTION_DELIMITER, MODEL_EOS_TOKEN, utterance_generator_client
    )
    parsed_action = action_parser(raw_output)

    # Verify the parsed action is correct
    assert parsed_action[0] == expected_action

    # Verify that there is a dialog action if EOS is included
    if include_eos:
        assert parsed_action[-1].type == SimBotActionType.Dialog

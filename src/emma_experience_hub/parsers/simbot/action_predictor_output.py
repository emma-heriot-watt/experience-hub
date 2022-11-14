from typing import Optional, Union

from loguru import logger
from overrides import overrides

from emma_experience_hub.constants.simbot import (
    get_simbot_objects_to_indices_map,
    get_simbot_room_names,
)
from emma_experience_hub.datamodels import EmmaExtractedFeatures
from emma_experience_hub.datamodels.simbot.actions import SimBotAction, SimBotActionType
from emma_experience_hub.datamodels.simbot.payloads import (
    SimBotGotoObjectPayload,
    SimBotGotoPayload,
    SimBotGotoRoomPayload,
    SimBotInteractionObject,
    SimBotObjectInteractionPayload,
    SimBotObjectMaskType,
    SimBotPayload,
)
from emma_experience_hub.parsers.parser import NeuralParser
from emma_experience_hub.parsers.simbot.functions import (
    SimBotDeconstructedAction,
    get_correct_frame_index,
    get_mask_from_special_tokens,
)


class SimBotActionPredictorOutputParser(NeuralParser[SimBotAction]):
    """Parse the correct action from the model output."""

    available_room_names: set[str] = get_simbot_room_names()

    _payget_to_action_type: dict[type[SimBotPayload], str] = {
        payload: action_type
        for action_type, payload in SimBotActionType.action_type_to_payload_model().items()
    }

    _object_label_to_idx: dict[str, int] = get_simbot_objects_to_indices_map()
    _lowercase_label_to_object_label: dict[str, str] = {
        object_label.lower(): object_label for object_label in _object_label_to_idx.keys()
    }

    def __init__(self, action_delimiter: str, eos_token: str) -> None:
        self._eos_token = eos_token
        self._action_delimiter = action_delimiter

    @overrides(check_signature=False)
    def __call__(
        self,
        decoded_trajectory: str,
        extracted_features: list[EmmaExtractedFeatures],
        num_frames_in_current_turn: int = 1,
    ) -> SimBotAction:
        """Convert the decoded trajectory to a sequence of SimBot actions."""
        logger.debug(f"Decoded trajectory: `{decoded_trajectory}`")

        try:
            decoded_action = self._separate_decoded_trajectory(decoded_trajectory)[0]
        except IndexError:
            # If there is a problem when decoding the action
            raise IndexError("Could not decode any actions from the trajectory")

        # Just use the first action, because if that is wrong, any future ones after it are likely
        # hallucinated
        deconstructed_action = SimBotDeconstructedAction.from_raw_action(decoded_action)

        return self.create_action_from_deconstructed_action(
            deconstructed_action, num_frames_in_current_turn, extracted_features
        )

    def create_action_from_deconstructed_action(
        self,
        deconstructed_action: SimBotDeconstructedAction,
        num_frames_in_current_turn: int,
        extracted_features: list[EmmaExtractedFeatures],
    ) -> SimBotAction:
        """Convert the deconstructed action into an executable form."""
        if deconstructed_action.action_type in SimBotActionType.low_level_navigation():
            return self.handle_low_level_navigation_action(deconstructed_action)

        if deconstructed_action.action_type in SimBotActionType.object_interaction():
            return self.handle_object_interaction_action(
                deconstructed_action, num_frames_in_current_turn, extracted_features
            )

        if deconstructed_action.action_type == SimBotActionType.Goto:
            return self.handle_goto_action(
                deconstructed_action, num_frames_in_current_turn, extracted_features
            )

        raise AssertionError("The action type cannot be converted to an executable form.")

    def handle_low_level_navigation_action(
        self, deconstructed_action: SimBotDeconstructedAction
    ) -> SimBotAction:
        """Return an executable low level navigation action."""
        return SimBotAction(
            id=0,
            type=deconstructed_action.action_type.base_type,
            payload=deconstructed_action.action_type.payload_model(),
            raw_output=deconstructed_action.raw_action,
        )

    def handle_object_interaction_action(
        self,
        deconstructed_action: SimBotDeconstructedAction,
        num_frames_in_current_turn: int,
        extracted_features: list[EmmaExtractedFeatures],
    ) -> SimBotAction:
        """Return an object interaction action."""
        mask, color_image_index = self._prepare_interaction_object_payload(
            deconstructed_action=deconstructed_action,
            num_frames_in_current_turn=num_frames_in_current_turn,
            extracted_features=extracted_features,
        )
        return SimBotAction(
            id=0,
            type=deconstructed_action.action_type,
            raw_output=deconstructed_action.raw_action,
            payload=SimBotObjectInteractionPayload(
                object=SimBotInteractionObject(
                    name=deconstructed_action.class_name,
                    colorImageIndex=color_image_index,
                    mask=mask,
                )
            ),
        )

    def handle_goto_action(
        self,
        deconstructed_action: SimBotDeconstructedAction,
        num_frames_in_current_turn: int,
        extracted_features: list[EmmaExtractedFeatures],
    ) -> SimBotAction:
        """Return an executable goto action."""
        payload: Union[SimBotGotoRoomPayload, SimBotGotoObjectPayload]

        if deconstructed_action.class_name in self.available_room_names:
            payload = SimBotGotoRoomPayload(officeRoom=deconstructed_action.class_name)
        else:
            mask, color_image_index = self._prepare_interaction_object_payload(
                deconstructed_action=deconstructed_action,
                num_frames_in_current_turn=num_frames_in_current_turn,
                extracted_features=extracted_features,
            )
            payload = SimBotGotoObjectPayload(
                name=deconstructed_action.class_name,
                colorImageIndex=color_image_index,
                mask=mask,
            )

        return SimBotAction(
            id=0,
            type=deconstructed_action.action_type,
            raw_output=deconstructed_action.raw_action,
            payload=SimBotGotoPayload(object=payload),
        )

    def _separate_decoded_trajectory(self, decoded_trajectory: str) -> list[str]:
        """Split the decoded trajectory string into a list of action strings.

        Uses the given action delimiter (which is likely going to be the tokenizer SEP token).

        Also removes any blank strings from the list of actions.
        """
        decoded_action_str = decoded_trajectory.replace(self._eos_token, "")
        split_actions = decoded_action_str.split(self._action_delimiter)
        actions = [action.strip() for action in split_actions if action]
        return actions

    def _prepare_interaction_object_payload(
        self,
        deconstructed_action: SimBotDeconstructedAction,
        extracted_features: list[EmmaExtractedFeatures],
        num_frames_in_current_turn: int,
    ) -> tuple[Optional[SimBotObjectMaskType], int]:
        if deconstructed_action.class_name == "stickynote":
            # TODO: are we sure that we want to assume that the sticky note is in frame 0?
            return None, 0

        color_image_index = get_correct_frame_index(
            deconstructed_action.frame_index,
            num_frames_in_current_turn,
            num_total_frames=len(extracted_features),
        )
        if not deconstructed_action.object_index:
            raise AssertionError("No object index token.")

        mask = get_mask_from_special_tokens(
            frame_index=deconstructed_action.frame_index,
            object_index=deconstructed_action.object_index,
            extracted_features=extracted_features,
        )

        return mask, color_image_index

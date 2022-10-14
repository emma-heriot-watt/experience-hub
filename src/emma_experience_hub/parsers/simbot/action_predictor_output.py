from typing import Literal, Optional, Union

import torch
from loguru import logger
from overrides import overrides
from pydantic import BaseModel

from emma_experience_hub.api.clients import UtteranceGeneratorClient
from emma_experience_hub.constants.model import END_OF_TRAJECTORY_TOKEN
from emma_experience_hub.constants.simbot import (
    ACTION_SYNONYMS,
    get_simbot_object_label_to_class_name_map,
    get_simbot_objects_to_indices_map,
    get_simbot_room_name_map,
    get_simbot_room_names,
)
from emma_experience_hub.datamodels import EmmaExtractedFeatures
from emma_experience_hub.datamodels.simbot.actions import SimBotAction, SimBotActionType
from emma_experience_hub.datamodels.simbot.payloads import (
    SimBotDialogPayload,
    SimBotInteractionObject,
    SimBotObjectInteractionPayload,
    SimBotPayload,
)
from emma_experience_hub.datamodels.simbot.payloads.navigation import (
    SimBotGotoObjectPayload,
    SimBotGotoPayload,
    SimBotGotoRoomPayload,
)
from emma_experience_hub.parsers.parser import NeuralParser


ObjectOutputType = Literal["OBJECT_CLASS", "OBJECT_MASK"]


class CompressSegmentationMask:
    """Refactored version of their compress mask function.

    Just to make a bit more sense of it.
    """

    __slots__ = ("run_idx", "run_length", "compressed_mask", "current_run")

    def __init__(self) -> None:
        self.run_idx = 0
        self.run_length = 0
        self.compressed_mask: list[list[int]] = []
        self.current_run = False

    def __call__(self, mask: torch.Tensor) -> list[list[int]]:
        """Compress the mask."""
        self.reset()

        for x_idx in range(mask.size(0)):
            for y_idx in range(mask.size(1)):
                self.step(mask, x_idx, y_idx)

        return self.compressed_mask

    def reset(self) -> None:
        """Reset the state of the class."""
        self.run_idx = 0
        self.run_length = 0
        self.compressed_mask = []
        self.current_run = False

    def step(self, mask: torch.Tensor, x_idx: int, y_idx: int) -> None:
        """Take step in loop."""
        if mask[x_idx][y_idx] == 1 and not self.current_run:
            self.start_new_run()

        if mask[x_idx][y_idx] == 0 and self.current_run:
            self.end_current_run()

        if self.current_run:
            self.run_length += 1

        self.run_idx += 1

    def start_new_run(self) -> None:
        """Start a new run to compress."""
        self.current_run = True
        self.compressed_mask.append([self.run_idx, 0])

    def end_current_run(self) -> None:
        """End the current run."""
        self.current_run = False
        self.compressed_mask[-1][1] = self.run_length
        self.run_length = 0


class SimBotActionParams(BaseModel):
    """Deconstructed SimBot action from the decoded action trajectory."""

    label: Optional[str] = None
    raw_label: Optional[str] = None
    object_visual_token: Optional[str] = None
    frame_index: int = 1

    @classmethod
    def from_decoded_action_params(  # noqa: WPS231
        cls, action_params: list[str]
    ) -> "SimBotActionParams":
        """Parse the decoded action params from the raw decoded params list."""
        label = None
        object_visual_token = None
        raw_label = None
        frame_index = 1

        for action_param in action_params:
            action_param = action_param.strip()

            if action_param.startswith("<vis_token") and action_param.endswith(">"):
                object_visual_token = action_param

            elif action_param.startswith("<frame") and action_param.endswith(">"):
                frame_index = int(action_param.strip().split("_")[-1].replace(">", ""))

            else:
                # in this case, we're trying to extract the class label which could be composed of
                # several tokens
                if raw_label is None:
                    raw_label = action_param
                else:
                    # concatenates the previous part of the label with the current one
                    raw_label = " ".join([raw_label, action_param])  # type: ignore[unreachable]

        if raw_label:
            label = raw_label

        return cls(
            label=label,
            raw_label=raw_label,
            frame_index=frame_index,
            object_visual_token=object_visual_token,
        )

    @property
    def class_name(self) -> str:
        """Get a string for the object label, no matter what."""
        label = self.dict().get("label")
        if not label:
            label = self.dict().get("raw_label")

        class_name: Optional[str] = None

        # Check if the label is an object
        if label:
            class_name = get_simbot_object_label_to_class_name_map(lowercase_keys=True).get(label)

        # Check if the label is a room name
        if label and not class_name:
            class_name = get_simbot_room_name_map().get(label)

        # If still nothing, return a blank string.
        if not class_name:
            raise AssertionError("Unable to get the class name from the label.")

        return class_name


class SimBotActionPredictorOutputParser(NeuralParser[SimBotAction]):
    """Parse the correct action from the model output."""

    available_room_names: set[str] = get_simbot_room_names()

    _synonym_to_action_map: dict[str, SimBotActionType] = {
        synonym: action
        for action, synonym_set in ACTION_SYNONYMS.items()
        for synonym in synonym_set
    }

    _payget_to_action_type: dict[type[SimBotPayload], str] = {
        payload: action_type
        for action_type, payload in SimBotActionType.action_type_to_payload_model().items()
    }

    _object_label_to_idx: dict[str, int] = get_simbot_objects_to_indices_map()
    _lowercase_label_to_object_label: dict[str, str] = {
        object_label.lower(): object_label for object_label in _object_label_to_idx.keys()
    }

    def __init__(
        self,
        action_delimiter: str,
        eos_token: str,
        utterance_generator_client: UtteranceGeneratorClient,
    ) -> None:
        self._eos_token = eos_token
        self._action_delimiter = action_delimiter

        self._utterance_generator_client = utterance_generator_client

    @overrides(check_signature=False)
    def __call__(
        self,
        decoded_trajectory: str,
        extracted_features: list[EmmaExtractedFeatures],
        num_frames_in_current_turn: int = 1,
    ) -> SimBotAction:
        """Convert the decoded trajectory to a sequence of SimBot actions."""
        logger.debug(f"Decoded trajectory: `{decoded_trajectory}`")

        decoded_actions_list = self._separate_decoded_trajectory(decoded_trajectory)

        # If there is a problem when decoding the action, ask the user for some help.
        if not decoded_actions_list:
            return self._return_ask_for_help_action()

        parsed_actions: list[SimBotAction] = []
        for decoded_action in decoded_actions_list:
            try:
                parsed_actions.append(
                    self._convert_action_to_executable_form(
                        decoded_action, num_frames_in_current_turn, extracted_features
                    )
                )

            # If there is a parsing issue, ask the user for help and don't decode any more
            # actions
            except Exception:
                logger.warning(f"Unable to decode the action: {decoded_action}")

        if not parsed_actions:
            return self._return_ask_for_help_action()

        return parsed_actions[0]

    def _separate_decoded_trajectory(self, decoded_trajectory: str) -> list[str]:
        """Split the decoded trajectory string into a list of action strings.

        Uses the given action delimiter (which is likely going to be the tokenizer SEP token).

        Also removes any blank strings from the list of actions.
        """
        decoded_action_str = decoded_trajectory.replace(self._eos_token, "")
        split_actions = decoded_action_str.split(self._action_delimiter)
        actions = [action.strip() for action in split_actions if action]

        # Remove the end of trajectory token the final action.
        actions[-1] = actions[-1].replace(END_OF_TRAJECTORY_TOKEN, "").strip()
        return actions

    def _get_simbot_action_from_tokens(
        self, action_tokens: list[str]
    ) -> tuple[SimBotActionType, list[str]]:
        """Get the SimBot action from the decoded action string.

        Assumptions:
            - The action appears at the start of the `decoded_action_string`.
            - The action can be of a length more than 1.

        Example:
            - If decoded_action == `forward`, then return `Forward`
            - If decoded_action == `pickup mug`, then return `Pickup`
        """
        parsed_action_name = None
        action_name = None

        index = len(action_tokens)

        while index > 0:
            action_name = " ".join(action_tokens[:index])

            if action_name.lower() in self._synonym_to_action_map:
                parsed_action_name = action_name.lower()
                break

            index -= 1

        # If we don't have an action type, then we don't really know what to do at all.
        if parsed_action_name is None:
            raise AssertionError("The action name could not be parsed.")

        return (
            self._synonym_to_action_map[parsed_action_name],
            action_tokens[index:],
        )

    def _convert_action_to_executable_form(
        self,
        action_str: str,
        num_frames_in_current_turn: int,
        extracted_features: list[EmmaExtractedFeatures],
    ) -> SimBotAction:
        """Convert the decoded action string into an executable form.

        We need to handle different cases:
            - Index 0: Should be the Simbot API Action
            - Index 1: Should be the object class (when available)
            - Index 2: Should be the visual token (when available)

        We are assuming that the visual token will only ever be present after the object class.
        """
        action_tokens = action_str.strip().split(" ")
        simbot_action_type, simbot_action_params = self._get_simbot_action_from_tokens(
            action_tokens
        )
        parsed_simbot_action_params = SimBotActionParams.from_decoded_action_params(
            simbot_action_params
        )

        if simbot_action_type in SimBotActionType.object_interaction():
            return self._return_object_interaction_simbot_action(
                simbot_action_type,
                parsed_simbot_action_params,
                num_frames_in_current_turn,
                extracted_features,
            )

        if simbot_action_type in SimBotActionType.low_level_navigation():
            return self._return_low_level_navigation_action(simbot_action_type)

        if simbot_action_type == SimBotActionType.Goto:
            return self._return_goto_action(
                simbot_action_type,
                parsed_simbot_action_params,
                num_frames_in_current_turn,
                extracted_features,
            )

        raise AssertionError("The action type cannot be converted to an executable form.")

    def _prepare_object_payload_params(  # noqa: WPS234
        self,
        parsed_action_params: SimBotActionParams,
        extracted_features: list[EmmaExtractedFeatures],
        num_frames_in_current_turn: int,
    ) -> tuple[Optional[list[list[int]]], int, ObjectOutputType]:
        if parsed_action_params.class_name == "stickynote":
            mask = None
            object_output_type = "OBJECT_CLASS"
            # TODO: are we sure that we want to assume that the sticky note is in frame 0?
            color_image_index = 0
        else:
            num_total_frames = len(extracted_features)
            color_image_index = self._get_correct_frame_index(
                parsed_action_params.frame_index,
                num_frames_in_current_turn,
                num_total_frames=num_total_frames,
            )
            mask = self._get_mask_from_visual_token(parsed_action_params, extracted_features)
            object_output_type = "OBJECT_MASK"

        return mask, color_image_index, object_output_type  # type: ignore[return-value]

    def _return_goto_action(
        self,
        action_type: SimBotActionType,
        parsed_action_params: SimBotActionParams,
        num_frames_in_current_turn: int,
        extracted_features: list[EmmaExtractedFeatures],
    ) -> SimBotAction:
        """Return an executable goto action."""
        payload: Union[SimBotGotoRoomPayload, SimBotGotoObjectPayload]

        object_output_type: ObjectOutputType = "OBJECT_CLASS"
        if parsed_action_params.class_name in self.available_room_names:
            payload = SimBotGotoRoomPayload(officeRoom=parsed_action_params.class_name)
        else:
            (mask, color_image_index, object_output_type) = self._prepare_object_payload_params(
                parsed_action_params=parsed_action_params,
                num_frames_in_current_turn=num_frames_in_current_turn,
                extracted_features=extracted_features,
            )

            payload = SimBotGotoObjectPayload(
                name=parsed_action_params.class_name,
                colorImageIndex=color_image_index,
                mask=mask,
            )

        return SimBotAction(
            type=action_type,
            payload=SimBotGotoPayload(object=payload),
            object_output_type=object_output_type,
        )

    def _return_low_level_navigation_action(self, action_type: SimBotActionType) -> SimBotAction:
        """Return an executable low level navigation action."""
        return SimBotAction(
            type=action_type.base_type,
            payload=action_type.payload_model(),
        )

    def _return_object_interaction_simbot_action(
        self,
        action_type: SimBotActionType,
        parsed_action_params: SimBotActionParams,
        num_frames_in_current_turn: int,
        extracted_features: list[EmmaExtractedFeatures],
    ) -> SimBotAction:
        """Return an executable object interaction action."""
        (mask, color_image_index, object_output_type) = self._prepare_object_payload_params(
            parsed_action_params=parsed_action_params,
            num_frames_in_current_turn=num_frames_in_current_turn,
            extracted_features=extracted_features,
        )
        return SimBotAction(
            type=action_type,
            payload=SimBotObjectInteractionPayload(
                object=SimBotInteractionObject(
                    name=parsed_action_params.class_name,
                    colorImageIndex=color_image_index,
                    mask=mask,
                )
            ),
            object_output_type=object_output_type,
        )

    def _return_ask_for_help_action(self) -> SimBotAction:
        """Return a dialog action when an exception or something unexpected occurs."""
        return SimBotAction(
            type=SimBotActionType.Dialog,
            payload=SimBotDialogPayload(
                value=self._utterance_generator_client.get_raised_exception_response()
            ),
        )

    def _get_mask_from_visual_token(  # noqa: WPS234
        self,
        deconstructed_action: SimBotActionParams,
        extracted_features: list[EmmaExtractedFeatures],
        return_coords: bool = False,
    ) -> Union[list[list[int]], tuple[list[list[int]], tuple[float, ...]]]:  # noqa: WPS221
        """Get the object mask from the visual token."""
        frame_index = deconstructed_action.frame_index

        # frame_index are 1-indexed
        object_coordinates_bbox = extracted_features[frame_index - 1].bbox_coords

        object_visual_token_str = deconstructed_action.object_visual_token
        # <vis_token_2>
        object_visual_token = int(
            object_visual_token_str.split("_")[-1][:-1]  # type:ignore[union-attr]
        )

        # visual tokens start are 1-indexed
        (x_min, y_min, x_max, y_max) = object_coordinates_bbox[object_visual_token - 1].tolist()

        mask = torch.zeros(
            (extracted_features[frame_index - 1].width, extracted_features[frame_index - 1].height)
        )
        # populate the bbox region in the mask with ones
        mask[int(y_min) : int(y_max) + 1, int(x_min) : int(x_max) + 1] = 1  # noqa: WPS221
        compressed_mask = CompressSegmentationMask()(mask)
        if return_coords:
            return compressed_mask, (x_min, y_min, x_max, y_max)
        return compressed_mask

    def _get_correct_frame_index(
        self,
        parsed_frame_index: int,
        num_frames_in_current_turn: int,
        num_total_frames: int,
    ) -> int:
        """Get the correct frame index, considering the number of frames in the current turn."""
        # Get the starting index frame for the current turn
        start_frame_index = num_total_frames - num_frames_in_current_turn + 1
        # Get the corrected frame index
        frame_index = parsed_frame_index - start_frame_index
        if num_frames_in_current_turn == 1 and frame_index != 0:
            logger.warning(f"Predicted frame index: {frame_index} instead of 0.")
            frame_index = 0
        else:
            # Make sure that the predicted frame index is between 0 and 3.
            frame_index = min(max(frame_index, 0), 3)
        return frame_index

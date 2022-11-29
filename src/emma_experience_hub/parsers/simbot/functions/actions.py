from typing import Optional

from pydantic import BaseModel

from emma_experience_hub.constants.model import END_OF_TRAJECTORY_TOKEN
from emma_experience_hub.constants.simbot import (
    ACTION_SYNONYMS,
    get_simbot_object_label_to_class_name_map,
    get_simbot_room_name_map,
)
from emma_experience_hub.datamodels.simbot import SimBotActionType
from emma_experience_hub.parsers.simbot.functions.special_tokens import (
    SimBotSceneObjectTokens,
    extract_index_from_special_token,
)


def get_simbot_action_from_tokens(
    action_tokens: list[str], synonym_to_action_map: dict[str, SimBotActionType]
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

        if action_name.lower() in synonym_to_action_map:
            parsed_action_name = action_name.lower()
            break

        index -= 1

    # If we don't have an action type, then we don't really know what to do at all.
    if parsed_action_name is None:
        raise AssertionError("The action name could not be parsed.")

    return (
        synonym_to_action_map[parsed_action_name],
        action_tokens[index:],
    )


class SimBotDeconstructedAction(BaseModel):
    """Deconstructed action for a given trajectory part."""

    _synonym_to_action_map: dict[str, SimBotActionType] = {
        synonym: action
        for action, synonym_set in ACTION_SYNONYMS.items()
        for synonym in synonym_set
    }

    action_type: SimBotActionType
    raw_action: str

    label: Optional[str] = None
    raw_label: Optional[str] = None

    special_tokens: SimBotSceneObjectTokens

    @classmethod
    def from_raw_action(cls, raw_action: str) -> "SimBotDeconstructedAction":
        """Deconstruct and parse the raw action."""
        # Remove the end of trajectory token from the action to process it. We
        # only care about it when figuring out the dialog.
        action_tokens = raw_action.replace(END_OF_TRAJECTORY_TOKEN, "").strip().split(" ")
        action_type, action_params = get_simbot_action_from_tokens(
            action_tokens, cls._synonym_to_action_map
        )
        return cls.from_raw_action_params(raw_action, action_type, action_params)

    @classmethod
    def from_raw_action_params(  # noqa: WPS231
        cls, raw_action: str, action_type: SimBotActionType, action_params: list[str]
    ) -> "SimBotDeconstructedAction":
        """Deconstruct and parse the raw action from the params."""
        label = None
        object_index = None
        raw_label = None
        frame_index = 1

        for action_param in action_params:
            action_param = action_param.strip()

            if action_param.startswith("<vis_token") and action_param.endswith(">"):
                object_index = extract_index_from_special_token(action_param)

            elif action_param.startswith("<frame") and action_param.endswith(">"):
                frame_index = extract_index_from_special_token(action_param)

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
            raw_action=raw_action,
            action_type=action_type,
            label=label,
            raw_label=raw_label,
            special_tokens=SimBotSceneObjectTokens(
                frame_index=frame_index, object_index=object_index
            ),
        )

    @property
    def object_index(self) -> Optional[int]:
        """Get the parsed object index."""
        return self.special_tokens.object_index

    @property
    def frame_index(self) -> int:
        """Get the parsed frame index."""
        return self.special_tokens.frame_index

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

        # If still nothing, return the raw label provided we have object visual token and the frame
        # token
        has_both_frame_and_object_indices = (
            self.object_index is not None and self.frame_index is not None
        )
        if label and not class_name and has_both_frame_and_object_indices:
            class_name = label

        # If it is still none, something has gone very wrong
        if not class_name:
            raise AssertionError("Unable to get the class name from the label.")

        return class_name

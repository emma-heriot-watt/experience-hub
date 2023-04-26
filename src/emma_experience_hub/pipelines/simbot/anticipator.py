from typing import Optional

import torch
from loguru import logger
from opentelemetry import trace

from emma_common.datamodels import SpeakerRole
from emma_experience_hub.api.clients.simbot import SimBotFeaturesClient, SimBotHacksClient
from emma_experience_hub.datamodels.simbot import SimBotIntent, SimBotIntentType, SimBotSession
from emma_experience_hub.datamodels.simbot.actions import SimBotAction
from emma_experience_hub.datamodels.simbot.enums import SimBotActionType
from emma_experience_hub.datamodels.simbot.queue import SimBotQueueUtterance
from emma_experience_hub.functions.simbot.special_tokens import extract_index_from_special_token


tracer = trace.get_tracer(__name__)


class SimbotAnticipatorPipeline:
    """Generate a plan of instructions and appends them to the utterance queue."""

    def __init__(
        self,
        simbot_hacks_client: SimBotHacksClient,
        features_client: SimBotFeaturesClient,
        _is_offline_evaluation: bool = False,
    ) -> None:
        self._simbot_hacks_client = simbot_hacks_client
        self._is_offline_evaluation = _is_offline_evaluation
        self._features_client = features_client

    def run(self, session: SimBotSession) -> None:
        """Generate an action to perform on the environment."""
        # Skip the anticipator during the offline evaluation
        if self._is_offline_evaluation:
            return

        # Do not run the anticipator pipeline if there are utterances in queue.
        # We dont want to add the utterances produced by the anticipator if
        # 1) the previous utterance has been split by the compound splitter, meaning there are still actions that the user asked us to perform or
        # 2) in some previous turn the anticipator produced already a plan that are now executing, therefore we dont want to override that plan.
        if session.current_state.utterance_queue.is_not_empty:
            return

        current_action = session.current_turn.actions.interaction
        if current_action is not None and current_action.is_end_of_trajectory:
            anticipator_output = self._simbot_hacks_client.get_anticipator_prediction_from_action(
                action=current_action,
                inventory_entity=session.current_turn.state.inventory.entity,
                entity_labels=self._get_relevant_entity_labels(session, current_action),
            )

            # If the anticipator has returned a sequence of instructions update the utterance queue
            if anticipator_output is None:
                return

            logger.debug(
                f"[Plan] Adding the plan utterances to the queue: {anticipator_output.utterances}"
            )
            session.current_state.utterance_queue.reset()
            session.current_state.utterance_queue.extend_tail(
                SimBotQueueUtterance(utterance=utterance, role=SpeakerRole.agent)
                for utterance in anticipator_output.utterances
            )

            if anticipator_output.requires_confirmation:
                # We also need to update the verbal interaction intent to confirm in order to
                # get the confirmation from the user in the next turn
                session.current_turn.intent.verbal_interaction = SimBotIntent(
                    type=SimBotIntentType.confirm_before_plan
                )

    def _get_relevant_entity_labels(
        self, session: SimBotSession, current_action: SimBotAction
    ) -> Optional[list[str]]:
        """Get relevant entity labels for the current action."""
        entity_labels = None
        # We only care about objects that overlap with the object that is being poured into
        if current_action.type == SimBotActionType.Pour and current_action.raw_output:
            try:
                entity_labels = self._get_labels_for_overlapping_entities(
                    session, current_action.raw_output
                )
            except Exception:
                logger.exception("Failed to get the labels for overlapping entities")
        return entity_labels

    def _add_coffee_maker(self, labels: list[str], all_objects: list[str]) -> list[str]:
        """Add the coffee maker to the list of labels if it is not already present."""
        # This will allow the anticipator to prioritize the coffee maker for the coffee pot
        if "Coffee Maker" in all_objects:
            labels.append("coffee maker")
        return labels

    def _get_labels_for_overlapping_entities(
        self, session: SimBotSession, raw_output: Optional[str]
    ) -> Optional[list[str]]:
        """Get the labels of the entities that are overlapping with the current action bbox."""
        if raw_output is None:
            return None
        # Get the index of the pour target object
        object_str_index = [
            action_param
            for action_param in raw_output.split(" ")
            if action_param.startswith("<vis_token")
        ]
        if not object_str_index:
            return None
        object_index = extract_index_from_special_token(object_str_index[0]) - 1
        features = self._features_client.get_features(session.current_turn)[-1]
        bbox_coords = features.bbox_coords
        current_action_bbox = bbox_coords[object_index]
        # Get the labels of the entities that overlap with the current action bbox
        entity_labels = features.entity_labels
        if entity_labels is None:
            return None
        left = torch.max(current_action_bbox[0], bbox_coords[:, 0])
        right = torch.min(current_action_bbox[2], bbox_coords[:, 2])
        bottom = torch.max(current_action_bbox[1], bbox_coords[:, 1])
        top = torch.min(current_action_bbox[3], bbox_coords[:, 3])
        overlap = torch.logical_not(torch.logical_or(left > right, bottom > top))
        labels = [label for label, is_overlapping in zip(entity_labels, overlap) if is_overlapping]
        return self._add_coffee_maker(labels, entity_labels)

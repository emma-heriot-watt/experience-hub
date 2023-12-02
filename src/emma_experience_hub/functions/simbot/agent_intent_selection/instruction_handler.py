from typing import Optional

from loguru import logger

from emma_common.datamodels import EnvironmentStateTurn, SpeakerRole
from emma_experience_hub.api.clients.simbot import (
    SimbotActionPredictionClient,
    SimBotFeaturesClient,
    SimBotHacksClient,
    SimBotNLUIntentClient,
)
from emma_experience_hub.datamodels.simbot import (
    SimBotAgentIntents,
    SimBotIntent,
    SimBotIntentType,
    SimBotNLUIntentType,
    SimBotSession,
    SimBotUserSpeech,
    SimBotUtterance,
)
from emma_experience_hub.datamodels.simbot.queue import SimBotQueueUtterance
from emma_experience_hub.parsers import NeuralParser
from emma_experience_hub.pipelines.simbot.compound_splitter import SimBotCompoundSplitterPipeline


class SimBotActHandler:
    """Determine the agent intents after a new instruction."""

    def __init__(
        self,
        features_client: SimBotFeaturesClient,
        nlu_intent_client: SimBotNLUIntentClient,
        nlu_intent_parser: NeuralParser[SimBotIntent[SimBotNLUIntentType]],
        action_predictor_client: SimbotActionPredictionClient,
        compound_splitter_pipeline: SimBotCompoundSplitterPipeline,
        simbot_hacks_client: SimBotHacksClient,
        _enable_clarification_questions: bool = True,
        _enable_confirmation_questions: bool = True,
        _enable_search_actions: bool = True,
        _enable_search_after_no_match: bool = True,
        _enable_search_after_missing_inventory: bool = True,
        _enable_high_level_planner: bool = True,
        _enable_simbot_raw_text_match: bool = True,
    ) -> None:
        self._features_client = features_client

        self._nlu_intent_client = nlu_intent_client
        self._nlu_intent_parser = nlu_intent_parser
        self._simbot_hacks_client = simbot_hacks_client
        self._action_predictor_client = action_predictor_client
        self._compound_splitter_pipeline = compound_splitter_pipeline

        self._enable_clarification_questions = _enable_clarification_questions
        self._enable_confirmation_questions = _enable_confirmation_questions
        self._enable_search_actions = _enable_search_actions
        self._enable_search_after_no_match = _enable_search_after_no_match
        self._enable_missing_inventory = _enable_search_after_missing_inventory
        self._enable_high_level_planner = _enable_high_level_planner
        self._enable_simbot_raw_text_match = _enable_simbot_raw_text_match

    def run(self, session: SimBotSession) -> Optional[SimBotAgentIntents]:
        """Get the agent intent."""
        # Check if the utterance has already been processed by the NLU
        if self._utterance_has_been_processed_by_nlu(session):
            logger.debug("Executing utterance that triggered the search.")
            return SimBotAgentIntents(
                physical_interaction=SimBotIntent(type=SimBotIntentType.act_one_match)
            )

        # Call the high-level planner
        if self._enable_high_level_planner:
            session = self._compound_splitter_pipeline.run_high_level_planner(session)
        # Check if the utterance matches one of the known templates
        if self._enable_simbot_raw_text_match:
            intents = self._process_utterance_with_raw_text_matcher(session)
            if intents is not None:
                return intents

        # Otherwise, use the NLU to detect it
        intents = self._process_utterance_with_nlu(session)
        if self._should_search_target_object(session, intents):
            intents = self._handle_act_no_match_intent(session=session, intents=intents)
        elif self._should_search_missing_inventory(session, intents):
            intents = self._handle_act_missing_inventory_intent(session=session, intents=intents)

        return self._handle_search_holding_object(session=session, intents=intents)

    def _utterance_has_been_processed_by_nlu(self, session: SimBotSession) -> bool:
        """Determine if the utterance has already been processed by the NLU.

        This happens when the intent was act no_match and search was completed.
        """
        return (
            session.previous_turn is not None
            and session.previous_turn.intent.is_searching_inferred_object
            and session.previous_turn.is_going_to_found_object_from_search
            and session.previous_turn.actions.is_successful
        )

    def _process_utterance_with_raw_text_matcher(  # noqa: WPS212
        self, session: SimBotSession
    ) -> Optional[SimBotAgentIntents]:
        """Use raw text matching to determine the agent's intent."""
        if not session.current_turn.speech:
            return None
        current_utterance = session.current_turn.speech.utterance

        # Check if the instruction matches an instruction template
        raw_text_match_prediction = (
            self._simbot_hacks_client.get_low_level_prediction_from_raw_text(
                utterance=current_utterance,
            )
        )
        if raw_text_match_prediction is not None:
            return SimBotAgentIntents(
                physical_interaction=SimBotIntent(type=SimBotIntentType.act_one_match)
            )

        # Check if the instruction requires us to change rooms
        room_text_match = self._simbot_hacks_client.get_room_prediction_from_raw_text(
            utterance=current_utterance,
        )
        # No room in the instruction
        if room_text_match is None:
            return None

        # Current room in the instruction
        if room_text_match.arena_room == session.current_turn.environment.current_room:
            return None

        # Check if we need to search for the inventory before going to the other room
        session.current_turn.speech = SimBotUserSpeech.update_user_utterance(
            utterance=room_text_match.modified_utterance,
            original_utterance=session.current_turn.speech.original_utterance,
        )
        intents = self._process_utterance_with_nlu(session)
        if self._should_search_missing_inventory(session, intents):
            return self._handle_act_missing_inventory_intent(
                session=session, intents=intents, target_room=room_text_match.arena_room
            )

        # Other room in the instruction
        queue_elem = SimBotQueueUtterance(
            utterance=room_text_match.modified_utterance, role=SpeakerRole.agent
        )
        session.current_state.utterance_queue.append_to_head(queue_elem)
        session.current_turn.speech = SimBotUserSpeech.update_user_utterance(
            utterance=f"go to the {room_text_match.room_name}",
            original_utterance=session.current_turn.speech.original_utterance,
        )
        return SimBotAgentIntents(
            physical_interaction=SimBotIntent(type=SimBotIntentType.act_one_match)
        )

    def _process_utterance_with_nlu(self, session: SimBotSession) -> SimBotAgentIntents:
        """Perform NLU on the utterance to determine what the agent should do next.

        This is primarily used to determine whether the agent should act or ask for more
        information.
        """
        extracted_features = self._features_client.get_features(session.current_turn)
        intent = self._nlu_intent_parser(
            self._nlu_intent_client.generate(
                dialogue_history=session.current_turn.utterances,
                environment_state_history=[EnvironmentStateTurn(features=extracted_features)],
                inventory_entity=session.current_state.inventory.entity,
            )
        )
        session.update_agent_memory(extracted_features)
        logger.debug(f"Extracted intent: {intent}")

        if not intent.type.triggers_question_to_user and session.current_turn.speech is not None:
            new_utterance = session.current_turn.speech.utterance.split("<<driver>>")[0].strip()
            session.current_turn.speech = SimBotUserSpeech(
                modified_utterance=SimBotUtterance(
                    utterance=new_utterance, role=session.current_turn.speech.role
                ),
                original_utterance=session.current_turn.speech.original_utterance,
            )

        if not self._enable_clarification_questions and intent.type.triggers_question_to_user:
            logger.info(
                "Clarification questions are disabled; returning the `<act><one_match>` intent."
            )
            return SimBotAgentIntents(
                physical_interaction=SimBotIntent(type=SimBotIntentType.act_one_match)
            )

        if self._should_replace_missing_inventory_intent(intent):
            logger.info(
                "Missing inventory search is disabled; returning the `<act><one_match>` intent."
            )
            return SimBotAgentIntents(
                physical_interaction=SimBotIntent(type=SimBotIntentType.act_one_match)
            )

        if not self._enable_search_actions and intent.type == SimBotIntentType.search:
            logger.info("Search actions are disabled; returning the `<act><one_match>` intent.")
            return SimBotAgentIntents(
                physical_interaction=SimBotIntent(type=SimBotIntentType.act_one_match)
            )

        if SimBotIntentType.is_physical_interaction_intent_type(intent.type):
            return SimBotAgentIntents(
                physical_interaction=SimBotIntent(
                    type=intent.type, action=intent.action, entity=intent.entity
                )
            )

        if SimBotIntentType.is_verbal_interaction_intent_type(intent.type):
            return SimBotAgentIntents(
                verbal_interaction=SimBotIntent(
                    type=intent.type, action=intent.action, entity=intent.entity
                ),
            )

        raise NotImplementedError(
            "All NLU intents are not accounted for. This means that NLU has returned an intent which does not map to either an interaction intent, or a response intent."
        )

    def _handle_act_no_match_intent(
        self, session: SimBotSession, intents: SimBotAgentIntents
    ) -> SimBotAgentIntents:
        """Update the session based on the NLU output.

        For `act_no_match`, push the current utterance in the utterance queue, and set the verbal
        interaction intent to `confirm_before_search`.
        """
        if intents.verbal_interaction is None:
            return intents
        # Make sure we know the object
        target_entity = intents.verbal_interaction.entity
        if target_entity is None:
            return intents

        # Confirm the search if we have not seen the object before
        if self._should_confirm_before_search(session, target_entity):
            return SimBotAgentIntents(
                verbal_interaction=SimBotIntent(
                    type=SimBotIntentType.confirm_before_search, entity=target_entity
                ),
            )
        # Otherwise start the search
        if not session.current_turn.speech.utterance.startswith("go to the"):  # type: ignore[union-attr]
            queue_elem = SimBotQueueUtterance(
                utterance=session.current_turn.speech.utterance,  # type: ignore[union-attr]
                role=SpeakerRole.user,
            )
            session.current_state.utterance_queue.append_to_head(queue_elem)
        session.current_turn.speech = SimBotUserSpeech.update_user_utterance(
            utterance=f"find the {target_entity}",
            role=SpeakerRole.agent,
            original_utterance=session.current_turn.speech.original_utterance
            if session.current_turn.speech is not None
            else None,
        )
        return SimBotAgentIntents(
            SimBotIntent(type=SimBotIntentType.search, entity=target_entity),
            SimBotIntent(
                type=SimBotIntentType.act_no_match,
                entity=target_entity,
            ),
        )

    def _handle_act_missing_inventory_intent(
        self,
        session: SimBotSession,
        intents: SimBotAgentIntents,
        target_room: Optional[str] = None,
    ) -> SimBotAgentIntents:
        """Update the session for `act_missing_inventory` intent.

        Search for the missing inventory, pick it up, and then execute the instruction.
        """
        # Make sure we know the missing object
        if intents.verbal_interaction is None:
            return intents
        target_entity = intents.verbal_interaction.entity
        if target_entity is None:
            return intents

        # If the agent is already holding an object, inform the user that we need to put it down
        if session.inventory.entity is not None:
            session.current_state.utterance_queue.reset()
            session.current_state.find_queue.reset()
            session.current_turn.intent.environment = SimBotIntent(
                type=SimBotIntentType.already_holding_object, entity=target_entity
            )
            return SimBotAgentIntents()

        # Put the current utterance in the queue
        queue_elem = SimBotQueueUtterance(
            utterance=session.current_turn.speech.utterance,  # type: ignore[union-attr]
            role=SpeakerRole.user,
        )
        session.current_state.utterance_queue.append_to_head(queue_elem)
        # Add a goto room utterance in the queue
        if target_room is not None:
            queue_elem = SimBotQueueUtterance(
                utterance=f"go to the {target_room}",
                role=SpeakerRole.agent,
            )
            session.current_state.utterance_queue.append_to_head(queue_elem)
        # Put a "pick up" utterance in the queue
        queue_elem = SimBotQueueUtterance(
            utterance=f"pick up the {target_entity}",
            role=SpeakerRole.agent,
        )
        session.current_state.utterance_queue.append_to_head(queue_elem)
        # Update the current turn speech to be a "find" utterance
        session.current_turn.speech = SimBotUserSpeech.update_user_utterance(
            utterance=f"find the {target_entity}",
            role=SpeakerRole.agent,
            original_utterance=session.current_turn.speech.original_utterance
            if session.current_turn.speech is not None
            else None,
        )
        return SimBotAgentIntents(
            SimBotIntent(type=SimBotIntentType.search, entity=target_entity),
            SimBotIntent(
                type=SimBotIntentType.act_missing_inventory,
                entity=target_entity,
            ),
        )

    def _handle_search_holding_object(
        self, session: SimBotSession, intents: SimBotAgentIntents
    ) -> SimBotAgentIntents:
        """Avoid searching for what we are holding."""
        # Are we holding an object?
        holding_object = session.inventory.entity
        if holding_object is None:
            return intents

        # Is the intent search or confirm before search?
        # If yes, get the object we will search for
        search_object = None
        physical_interaction_intent = intents.physical_interaction
        verbal_interaction_intent = intents.verbal_interaction
        if physical_interaction_intent is not None:
            if physical_interaction_intent.type == SimBotIntentType.search:
                search_object = physical_interaction_intent.entity
        elif verbal_interaction_intent is not None:
            if verbal_interaction_intent.type == SimBotIntentType.confirm_before_search:
                search_object = verbal_interaction_intent.entity

        # If we are not searching for an object, continue with the extracted intents
        if search_object is None:
            return intents

        # Compare the search object with the holding object
        # If they are the same, assign an already_holding_object error
        if search_object == holding_object.lower():
            session.current_state.utterance_queue.reset()
            session.current_state.find_queue.reset()
            session.current_turn.intent.environment = SimBotIntent(
                type=SimBotIntentType.already_holding_object, entity=search_object
            )
            return SimBotAgentIntents()
        return intents

    def _should_confirm_before_search(self, session: SimBotSession, target_entity: str) -> bool:
        """Should the agent ask for confirmation before searching?"""
        if not self._enable_confirmation_questions:
            return False
        # Don't ask if we've seen the entity in the current room or know its location from prior memory
        has_seen_object = session.current_state.memory.object_in_memory(
            target_entity, current_room=session.current_turn.environment.current_room
        )
        return not has_seen_object

    def _should_search_target_object(
        self, session: SimBotSession, intents: SimBotAgentIntents
    ) -> bool:
        """Check the conditions for an act_no_match intent to trigger a search."""
        if intents.verbal_interaction is None or not self._enable_search_after_no_match:
            return False
        # Check the intent is act_no_match from a new utterance
        should_search_before_executing_instruction = (
            intents.verbal_interaction.type == SimBotIntentType.act_no_match
            and session.current_turn.speech is not None
        )
        return should_search_before_executing_instruction

    def _should_search_missing_inventory(
        self, session: SimBotSession, intents: SimBotAgentIntents
    ) -> bool:
        """Check the conditions for an act_missing_inventory intent to trigger a search."""
        if intents.verbal_interaction is None or not self._enable_missing_inventory:
            return False
        # Check the intent is act_missing_inventory from a new utterance
        should_search_before_executing_instruction = (
            intents.verbal_interaction.type == SimBotIntentType.act_missing_inventory
            and session.current_turn.speech is not None
        )
        return should_search_before_executing_instruction

    def _should_replace_missing_inventory_intent(
        self, intent: SimBotIntent[SimBotNLUIntentType]
    ) -> bool:
        """Is the missing inventory intent disabled?"""
        return (
            not self._enable_missing_inventory
            and intent.type == SimBotIntentType.act_missing_inventory
        )

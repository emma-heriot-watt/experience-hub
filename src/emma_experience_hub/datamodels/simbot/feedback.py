import string
from collections import Counter
from typing import Any, Optional

import orjson
from pydantic import BaseModel, Field, validator
from rule_engine import Context, Rule
from rule_engine.ast import ExpressionBase, SymbolExpression

from emma_experience_hub.datamodels.simbot.actions import SimBotAction
from emma_experience_hub.datamodels.simbot.enums import SimBotActionType, SimBotIntentType
from emma_experience_hub.datamodels.simbot.intents import SimBotIntent


def get_score_for_rule_expression(
    expression: ExpressionBase, left_attr_name: str = "left", right_attr_name: str = "right"
) -> int:
    """Get the score for expression within the rule.

    The conditions for each rule are converted into a binary tree. Therefore, we can recursively
    iterate over all the nodes within the tree to get the score as the number of conditions in the
    rule. Therefore, the more specific the rule the higher its score.
    """
    # Try to get the left and right nodes within the expression
    left_node: Optional[ExpressionBase] = getattr(expression, left_attr_name, None)
    right_node: Optional[ExpressionBase] = getattr(expression, right_attr_name, None)

    # If the left node is a SymBolExpression, we are at the slot name and can go no lower
    if isinstance(left_node, SymbolExpression):
        return 1

    # Otherwise, both nodes are not None, we can dig into them further to try and get the score
    if left_node is not None and right_node is not None:
        left_expression_score = get_score_for_rule_expression(
            left_node, left_attr_name, right_attr_name
        )
        right_expression_score = get_score_for_rule_expression(
            right_node, left_attr_name, right_attr_name
        )
        return left_expression_score + right_expression_score

    # If none of the above conditions suit, return 0 for this expression
    return 0


class SimBotFeedbackRule(BaseModel):
    """Rule for response generation."""

    id: int = Field(..., description="Unique rule id")
    rule: Rule = Field(..., description="Logical expression of the rule")
    response: str = Field(
        ...,
        description="Response template that can include slots. Slot values are derived from the `SimBotFeedbackState`",
    )
    is_lightweight_dialog: bool = Field(
        ..., description="Should the response be a lightweight dialog action"
    )
    score: int = Field(default=0, description="Determined by the number of conditions in the rule")

    class Config:
        """Updated config."""

        arbitrary_types_allowed = True

    @property
    def slot_names(self) -> list[str]:
        """Get the necessary slot names."""
        slot_names: list[str] = [
            name for _, name, _, _ in string.Formatter().parse(self.response) if name
        ]
        return slot_names

    def prepare_response(self, slots: Optional[dict[str, str]] = None) -> str:
        """Build the response for the given rule.

        If the rule is a template that requires slots to be filled, then slots need to be provided
        and this method will raise an exception if all slots are not filled.
        """
        if self.slot_names and not slots:
            raise AssertionError(
                "We should be providing slot-value pairs for the response template."
            )

        if self.slot_names and slots:
            return self.response.format(**slots)

        return self.response

    @classmethod
    def from_raw(cls, raw_dict: dict[str, str]) -> "SimBotFeedbackRule":
        """Parse a dictionary into a SimBotFeedbackRule."""
        # If the rule is unable to resolve symbols, it defaults to None and returns False
        engine_context = Context(default_value=None)
        rule = Rule(raw_dict["conditions"], context=engine_context)

        rule_id = int(raw_dict["id"])

        if not rule.is_valid(rule.text):
            raise AssertionError(f"Invalid rule: ID {rule_id} - {rule.text}")

        return cls(
            id=rule_id,
            rule=rule,
            response=raw_dict["response"],
            is_lightweight_dialog=raw_dict["is_lightweight"] == "True",
            score=len(rule.context.symbols),
        )

    @validator("score", always=True)
    @classmethod
    def calculate_rule_score(cls, score: int, values: dict[str, Any]) -> int:  # noqa: WPS110
        """Calculate the score for the rule."""
        # If the score is not 0, then just return it
        if score > 1:
            return score

        # Get the rule and make sure it exists
        rule: Optional[Rule] = values.get("rule")
        if not rule:
            raise AssertionError("There should be a rule for this model?")

        # The score for a rule is the number of different criterion within it
        score = get_score_for_rule_expression(rule.statement.expression)

        if score < 1:
            raise AssertionError("Score should not be less than 1.")

        return score

    def is_query_suitable(self, query: dict[str, Any]) -> bool:
        """Evaluate the rule given the query and ensure it is suitable."""
        try:
            return self.rule.matches(query) and all([name in query for name in self.slot_names])
        except Exception:
            return False


class SimBotFeedbackState(BaseModel):
    """Flattened representation of the session state for feedback generation."""

    # Force query for a lightweight dialog
    require_lightweight_dialog: bool = False

    # Session statistics
    num_turns: int

    # Location
    current_room: str

    # Count all of the rooms visited
    visited_room_counter: Counter[str]

    # User intent
    user_intent_type: Optional[SimBotIntentType] = None

    # Environment intent
    environment_intent_type: Optional[SimBotIntentType] = None
    environment_intent_action_type: Optional[SimBotActionType] = None
    environment_intent_entity: Optional[str] = None

    # Agent intent
    agent_intent_type: Optional[SimBotIntentType] = None
    agent_intent_entity: Optional[str] = None
    agent_interaction_action: Optional[SimBotActionType] = None
    agent_interaction_entity: Optional[str] = None

    # History of actions taken in the session
    interaction_action_per_turn: list[SimBotAction]

    # Counter of how many times each action was taken
    action_type_counter: Counter[str]

    # History of all the AGENT intents in the session
    agent_intent_per_turn: list[SimBotIntent]

    # Counter of how many times each AGENT intent was held
    agent_intent_type_counter: Counter[str]

    # There are more instructions to execute from the latest user utterance
    utterance_queue_not_empty: bool

    # There are more instructions to execute from the find routine
    find_queue_not_empty: bool = False
    previous_find_queue_not_empty: bool = False

    # Histpry of used rule ids
    used_rule_ids: list[int] = Field(default_factory=list)

    class Config:
        """Config for the model."""

        json_encoders = {
            # Use the action type name when converting to the JSON response
            SimBotActionType: lambda action_type: action_type.name,
            # Use the intent type name when converting to the JSON response
            SimBotIntentType: lambda intent_type: intent_type.name,
        }

    @classmethod
    def from_all_information(
        cls,
        num_turns: int,
        current_room: str,
        user_intent_type: Optional[SimBotIntentType],
        environment_intent: Optional[SimBotIntent],
        agent_intent: Optional[SimBotIntent],
        agent_interaction_action: Optional[SimBotAction],
        current_room_per_turn: list[str],
        interaction_action_per_turn: list[SimBotAction],
        agent_intent_per_turn: list[SimBotIntent],
        utterance_queue_not_empty: bool,
        find_queue_not_empty: bool,
        previous_find_queue_not_empty: bool,
        used_rule_ids: list[int],
    ) -> "SimBotFeedbackState":
        """Create the state in a simple way."""
        return cls(
            # Require a lightweight dialog action when the model does not decode a <stop token
            require_lightweight_dialog=not agent_interaction_action.is_end_of_trajectory
            if agent_interaction_action
            else False,
            num_turns=num_turns,
            current_room=current_room,
            user_intent_type=user_intent_type,
            environment_intent_type=environment_intent.type if environment_intent else None,
            environment_intent_action_type=environment_intent.action
            if environment_intent
            else None,
            environment_intent_entity=environment_intent.entity if environment_intent else None,
            agent_intent_type=agent_intent.type if agent_intent else None,
            agent_intent_entity=agent_intent.entity if agent_intent else None,
            agent_interaction_action=agent_interaction_action.type
            if agent_interaction_action
            else None,
            agent_interaction_entity=agent_interaction_action.payload.entity_name
            if agent_interaction_action
            else None,
            visited_room_counter=Counter[str](current_room_per_turn),
            interaction_action_per_turn=interaction_action_per_turn,
            action_type_counter=Counter[str](
                action.type.name for action in interaction_action_per_turn
            ),
            agent_intent_per_turn=agent_intent_per_turn,
            agent_intent_type_counter=Counter[str](
                intent.type.name for intent in agent_intent_per_turn
            ),
            utterance_queue_not_empty=utterance_queue_not_empty,
            find_queue_not_empty=find_queue_not_empty,
            previous_find_queue_not_empty=previous_find_queue_not_empty,
            used_rule_ids=used_rule_ids,
        )

    def to_query(self) -> dict[str, Any]:
        """Convert the state to a dictionary for the feedback engine."""
        model_as_json = self.json(exclude_unset=True, exclude_defaults=True, exclude_none=True)
        model_as_dict = orjson.loads(model_as_json)
        return model_as_dict

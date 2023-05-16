from typing import Any, Optional

from pydantic import (
    AnyHttpUrl,
    BaseModel,
    BaseSettings,
    DirectoryPath,
    Field,
    root_validator,
    validator,
)

from emma_experience_hub.datamodels.common import GFHLocationType
from emma_experience_hub.datamodels.enums import SearchPlannerType


class SimBotFeatureArgs(BaseModel):
    """Optional arguments for the SimBot agent."""

    scan_area_threshold: float = 200


class SimBotFeatureFlags(BaseModel):
    """Feature flags for the SimBot agent."""

    enable_offline_evaluation: bool = True

    enable_always_highlight_before_object_action: bool = False
    enable_clarification_questions: bool = True
    enable_compound_splitting: bool = True
    enable_coreference_resolution: bool = True
    enable_confirmation_questions: bool = True
    enable_grab_from_history: bool = True
    enable_prior_memory: bool = True
    enable_incomplete_utterances_intent: bool = True
    enable_object_related_questions_from_user: bool = True
    enable_out_of_domain_detector: bool = True
    enable_profanity_filter: bool = True
    enable_rasa_high_level_planner: bool = False
    enable_scanning_during_search: bool = True
    enable_search_actions: bool = True
    enable_search_after_missing_inventory: bool = True
    enable_search_after_no_match: bool = True
    enable_simbot_qa: bool = True

    prevent_default_response_as_lightweight: bool = True

    search_planner_type: SearchPlannerType = SearchPlannerType.greedy_max_vertex_cover
    gfh_location_type: GFHLocationType = GFHLocationType.location

    @root_validator
    @classmethod
    def set_offline_evaluation_flags(
        cls,
        values: dict[str, Any],  # noqa: WPS110
    ) -> dict[str, Any]:
        """Make sure that flags are set correctly for the offline evaluation."""
        if values.get("enable_offline_evaluation", False):
            values["enable_clarification_questions"] = False
            values["enable_compound_splitting"] = False
            values["enable_coreference_resolution"] = False
            values["enable_prior_memory"] = False
            values["enable_confirmation_questions"] = False
            values["enable_incomplete_utterances_intent"] = False
            values["enable_object_related_questions_from_user"] = False
            values["enable_out_of_domain_detector"] = False
            values["enable_profanity_filter"] = False
            values["enable_scanning_during_search"] = False
            values["enable_search_after_missing_inventory"] = False
            values["enable_simbot_qa"] = False
            values["do_not_return_default_response_as_lightweight_response"] = False

            values["gfh_location_type"] = GFHLocationType.viewpoint
        return values


class SimBotSettings(BaseSettings):
    """Settings for the SimBot-related modules."""

    feature_flags: SimBotFeatureFlags = SimBotFeatureFlags()
    feature_arguments: SimBotFeatureArgs = SimBotFeatureArgs()

    host: str = "0.0.0.0"  # noqa: S104
    port: int = 5000
    scheme: str = "http"

    client_timeout: Optional[int] = 5

    aws_profile: str = Field(default="TeamProfile", env="aws_profile")

    watchtower_log_group_name: str = "simbot_challenge"
    opensearch_service_name: str = "experience-hub"
    watchtower_log_stream_name: str = "experience-hub/{machine_name}/{logger_name}/{process_id}"

    simbot_cache_s3_bucket: str = "emma-simbot-live-challenge"

    auxiliary_metadata_dir: DirectoryPath
    auxiliary_metadata_cache_dir: DirectoryPath

    extracted_features_cache_dir: DirectoryPath

    session_db_memory_table_name: str = "SIMBOT_MEMORY_TABLE"
    session_db_region: str = "us-east-1"

    feature_extractor_url: AnyHttpUrl = AnyHttpUrl(url=f"{scheme}://0.0.0.0:5500", scheme=scheme)

    nlu_predictor_url: AnyHttpUrl = AnyHttpUrl(url=f"{scheme}://0.0.0.0:5501", scheme=scheme)
    nlu_predictor_intent_type_delimiter: str = " "

    profanity_filter_url: AnyHttpUrl = AnyHttpUrl(url=f"{scheme}://0.0.0.0:5503", scheme=scheme)

    action_predictor_url: AnyHttpUrl = AnyHttpUrl(url=f"{scheme}://0.0.0.0:5502", scheme=scheme)

    out_of_domain_detector_url: AnyHttpUrl = AnyHttpUrl(
        url=f"{scheme}://0.0.0.0:5505", scheme=scheme
    )

    asr_avg_confidence_threshold: float = 0.55

    confirmation_classifier_url: AnyHttpUrl = AnyHttpUrl(
        url=f"{scheme}://0.0.0.0:5507", scheme=scheme
    )

    compound_splitter_url: AnyHttpUrl = AnyHttpUrl(url=f"{scheme}://0.0.0.0:5508", scheme=scheme)

    simbot_hacks_url: AnyHttpUrl = AnyHttpUrl(url=f"{scheme}://0.0.0.0:5509", scheme=scheme)

    simbot_qa_url: AnyHttpUrl = AnyHttpUrl(url=f"{scheme}://0.0.0.0:5510", scheme=scheme)

    otlp_endpoint: AnyHttpUrl = AnyHttpUrl(url=f"{scheme}://localhost:4317", scheme=scheme)

    placeholder_vision_url: AnyHttpUrl = AnyHttpUrl(url=f"{scheme}://0.0.0.0:5506", scheme=scheme)

    class Config:
        """Config for the settings."""

        env_prefix = "SIMBOT_"
        env_nested_delimiter = "__"

    @classmethod
    def from_env(cls) -> "SimBotSettings":
        """Instantiate from the environment variables."""
        return cls.parse_obj({})

    @validator("client_timeout")
    @classmethod
    def fix_timeout(cls, timeout: Optional[int]) -> Optional[int]:
        """Fix the timeout for httpx clients."""
        if timeout is not None and timeout < 0:
            return None

        return timeout

    @property
    def is_not_offline_evaluation(self) -> bool:
        """Are we not running the offline evaluation?"""
        return not self.feature_flags.enable_offline_evaluation


class SimBotRoomSearchBudget(BaseModel):
    """Seach budget settings."""

    viewpoint_budget: int = 3
    distance_threshold: float = 3.0

from typing import Any, Optional

from pydantic import AnyHttpUrl, BaseModel, BaseSettings, DirectoryPath, root_validator, validator

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
    enable_grab_from_history: bool = True
    enable_scanning_during_search: bool = True
    enable_search_actions: bool = True
    enable_search_after_missing_inventory: bool = True
    enable_search_after_no_match: bool = True

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
            values["enable_scanning_during_search"] = False
            values["enable_search_after_missing_inventory"] = False

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

    auxiliary_metadata_dir: DirectoryPath
    auxiliary_metadata_cache_dir: DirectoryPath

    extracted_features_cache_dir: DirectoryPath

    session_db_memory_table_name: str = "SIMBOT_MEMORY_TABLE"
    session_local_db_file: str = "storage/local_sessions.db"

    feature_extractor_url: AnyHttpUrl = AnyHttpUrl(url=f"{scheme}://0.0.0.0:5500", scheme=scheme)

    cr_predictor_url: AnyHttpUrl = AnyHttpUrl(url=f"{scheme}://0.0.0.0:5501", scheme=scheme)
    cr_predictor_intent_type_delimiter: str = " "

    action_predictor_url: AnyHttpUrl = AnyHttpUrl(url=f"{scheme}://0.0.0.0:5502", scheme=scheme)

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

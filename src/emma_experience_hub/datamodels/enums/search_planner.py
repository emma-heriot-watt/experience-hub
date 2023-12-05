from enum import Enum


class SearchPlannerType(Enum):
    """Available planner types."""

    basic = "basic"
    greedy_max_vertex_cover = "greedy_max_vertex_cover"

import itertools

import typer
from pydantic import BaseModel, Field, parse_file_as
from rich import box
from rich.live import Live
from rich.spinner import Spinner
from rich.table import Table

from emma_experience_hub.commands.teach.constants import TEAChPaths


class EDHInstanceMetrics(BaseModel):
    """Metrics for a single EDH instance."""

    instance_id: str
    game_id: str

    # Goal Conditions
    completed_goal_conditions: int
    total_goal_conditions: int
    goal_condition_success: float

    success_spl: float
    path_len_weighted_success_spl: float
    goal_condition_spl: float
    path_len_weighted_goal_condition_spl: float
    ground_truth_path_length: float = Field(..., alias="gt_path_len")

    reward: float
    success: bool
    trajectory_length: int = Field(..., alias="traj_len")

    predicted_stop: bool
    num_api_fails: int
    error: int
    init_success: bool


class SummaryMetrics(BaseModel):
    """Summary metrics, aggregated from all instances."""

    # Success Rate
    num_successes: int
    num_trials: int

    # Goal Conditions
    completed_goal_conditions: int
    total_goal_conditions: int

    # Path-Length Weighted
    plw_success_rate: float
    plw_goal_condition_success_rate: float

    @property
    def success_rate(self) -> float:
        """Get the success rate."""
        if self.num_trials == 0:
            return 0

        return self.num_successes / self.num_trials

    @property
    def goal_condition_success_rate(self) -> float:
        """Get the success rate."""
        if self.total_goal_conditions == 0:
            return 0

        return self.completed_goal_conditions / self.total_goal_conditions

    @classmethod
    def from_all_edh_instances(
        cls, all_individual_metrics: list[EDHInstanceMetrics]
    ) -> "SummaryMetrics":
        """Create a SummaryMetrics from all the individual metrics."""
        num_successes = sum(instance.success for instance in all_individual_metrics)
        num_trials = len(all_individual_metrics)

        completed_goal_conditions = sum(
            instance.completed_goal_conditions for instance in all_individual_metrics
        )
        total_goal_conditions = sum(
            instance.total_goal_conditions for instance in all_individual_metrics
        )

        total_path_length = sum(
            instance.ground_truth_path_length for instance in all_individual_metrics
        )

        if total_path_length > 0:
            # PLW == Path Length Weighted
            plw_success_rate = (
                sum(instance.path_len_weighted_success_spl for instance in all_individual_metrics)
                / total_path_length
            )
            plw_goal_condition_success_rate = (
                sum(
                    instance.path_len_weighted_goal_condition_spl
                    for instance in all_individual_metrics
                )
                / total_path_length
            )
        else:
            plw_success_rate = 0
            plw_goal_condition_success_rate = 0

        return cls(
            num_successes=num_successes,
            num_trials=num_trials,
            completed_goal_conditions=completed_goal_conditions,
            total_goal_conditions=total_goal_conditions,
            # total_path_length=total_path_length,
            plw_success_rate=plw_success_rate,
            plw_goal_condition_success_rate=plw_goal_condition_success_rate,
        )


def render_summary_metrics_table(metrics: SummaryMetrics) -> Table:
    """Render the results table from the metrics."""
    table = Table(
        expand=True,
        box=box.SIMPLE_HEAD,
        pad_edge=False,
        border_style="bright_yellow",
    )

    table.add_column()
    table.add_column("Successful/Total", justify="right")
    table.add_column("Average", justify="right")
    table.add_column("Path-length Weighted Avg.", justify="right")

    table.add_row(
        Spinner("dots", text="Overall Success"),
        f"{metrics.num_successes}/{metrics.num_trials}",
        f"{metrics.success_rate:.3f}",
        f"{metrics.plw_success_rate:.3f}",
    )

    table.add_row(
        Spinner("dots", text="Goal Condition"),
        f"{metrics.completed_goal_conditions}/{metrics.total_goal_conditions}",
        f"{metrics.goal_condition_success_rate:.3f}",
        f"{metrics.plw_goal_condition_success_rate:.3f}",
    )

    return table


def get_metrics_from_output_dir() -> list[EDHInstanceMetrics]:
    """Get all the metrics from the output metrics files."""
    all_metrics_files = (
        file_path
        for file_path in TEAChPaths.output_metadata.iterdir()
        if file_path.stem.startswith("metrics")
    )

    all_instance_metrics_per_file = (
        parse_file_as(dict[str, EDHInstanceMetrics], metric_file).values()
        for metric_file in all_metrics_files
    )

    all_instance_metrics = list(itertools.chain.from_iterable(all_instance_metrics_per_file))

    return all_instance_metrics


def create_summary_metrics_table() -> Table:
    """Create the summary metrics table and return the renderable."""
    all_metrics = get_metrics_from_output_dir()
    summary_metrics = SummaryMetrics.from_all_edh_instances(all_metrics)
    return render_summary_metrics_table(summary_metrics)


def compute_metrics(
    watch: bool = typer.Option(default=False, help="Watch the metrics for changes")
) -> None:
    """Aggregate and compute metrics from all the EDH instances."""
    with Live(create_summary_metrics_table()) as live:
        while watch:
            table = create_summary_metrics_table()
            table.caption = "[i]Press CTRL-C to exit.[/]"

            live.update(table)


if __name__ == "__main__":
    compute_metrics()

from typing import Optional

import typer

from emma_experience_hub.commands.teach.api import (
    launch_api,
    launch_feature_extractor_api,
    stop_api,
    stop_feature_extractor_api,
)
from emma_experience_hub.commands.teach.constants import TEAChDatasetSplit
from emma_experience_hub.commands.teach.dataset import (
    filter_edh_instances,
    restore_filtered_edh_instances,
)
from emma_experience_hub.commands.teach.download import (
    download_edh_instances,
    download_games,
    download_models,
    download_teach_data,
)
from emma_experience_hub.commands.teach.inference import (
    launch_inference_runner,
    machine_supports_inference_without_display,
    prepare_inference_runner,
    stop_inference_runner_container,
)
from emma_experience_hub.commands.teach.metrics import compute_metrics
from emma_experience_hub.commands.teach.xserver import launch_xserver


app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    short_help="Setup and run EMMA with TEACh.",
    help="Simplified commands for setup and running TEACh with EMMA.",
)


@app.command()
def prepare_everything(
    remote_perception_model_uri: str = typer.Option(
        ..., envvar="REMOTE_PERCEPTION_MODEL_URI", help="URI for the Perception model file on S3."
    ),
    remote_policy_model_uri: str = typer.Option(
        ..., envvar="REMOTE_POLICY_MODEL_URI", help="URI for the Policy model file on S3."
    ),
    count: Optional[int] = typer.Option(
        None,
        help="Optionally, only download a given number of instances for each dataset split.",
    ),
) -> None:
    """Prepare everything to run TEAch without thinking about it."""
    confirm = typer.confirm(
        "This will download and build everything and might take some time. Are you sure you want to continue?"
    )

    if not confirm:
        raise typer.Abort()

    download_models(remote_perception_model_uri, remote_policy_model_uri)
    download_games()
    download_edh_instances(TEAChDatasetSplit.valid_seen, count)
    download_edh_instances(TEAChDatasetSplit.valid_unseen, count)
    prepare_inference_runner(with_display=True, force_reset=True)

    if machine_supports_inference_without_display():
        prepare_inference_runner(with_display=False, force_reset=True)


app.command(rich_help_panel="Download Commands")(download_models)
app.command(rich_help_panel="Download Commands")(download_teach_data)
app.command(rich_help_panel="Download Commands")(download_games)
app.command(rich_help_panel="Download Commands")(download_edh_instances)

app.command(rich_help_panel="API Commands")(launch_api)
app.command(rich_help_panel="API Commands")(stop_api)
app.command(rich_help_panel="API Commands")(launch_feature_extractor_api)
app.command(rich_help_panel="API Commands")(stop_feature_extractor_api)

app.command(rich_help_panel="Metrics Commands")(compute_metrics)

app.command(rich_help_panel="Inference Runner Commands")(prepare_inference_runner)
app.command(rich_help_panel="Inference Runner Commands")(launch_inference_runner)
app.command(rich_help_panel="Inference Runner Commands")(launch_xserver)
app.command(rich_help_panel="Inference Runner Commands")(stop_inference_runner_container)

app.command(rich_help_panel="Dataset Commands")(filter_edh_instances)
app.command(rich_help_panel="Dataset Commands")(restore_filtered_edh_instances)

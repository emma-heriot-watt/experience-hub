import subprocess
from pathlib import Path

import typer
from rich.console import Console

from emma_experience_hub.commands.teach.constants import (
    API_CONTAINER_NAME,
    DOCKER_NETWORK_NAME,
    FEATURE_EXTRACTOR_CONTAINER_NAME,
    FEATURE_EXTRACTOR_DEFAULT_PORT,
    MODEL_DIR_WITHIN_CONTAINER,
    POLICY_API_DEFAULT_PORT,
    TEAChDatasetSplit,
    TEAChPaths,
)
from emma_experience_hub.common.docker import create_network_if_not_exists, stop_container
from emma_experience_hub.common.system import (
    is_xserver_display_running,
    machine_supports_inference_without_display,
)
from emma_experience_hub.common.torch import is_cuda_available


console = Console()


def launch_feature_extractor_api(
    api_port: int = typer.Option(
        default=FEATURE_EXTRACTOR_DEFAULT_PORT,
        help="Exposed API port for the feature extractor API.",
    ),
    log_level: str = typer.Option("debug", envvar="LOG_LEVEL", help="Log level for the API"),
    use_gpu: bool = typer.Option(
        default=is_cuda_available(), help="Run using GPU", show_envvar=False
    ),
) -> None:
    """Launch the feature extractor API for TEACh.

    This is useful for debugging inference with Policy.
    """
    # Stop the container if it is running already.
    stop_feature_extractor_api()

    paths = TEAChPaths()

    command = [
        "docker",
        "run",
        "--rm",
        f"--name {FEATURE_EXTRACTOR_CONTAINER_NAME}",
        f"-p {api_port}:{FEATURE_EXTRACTOR_DEFAULT_PORT}",
        '--gpus "device=0"' if use_gpu else "",
        f"-v {paths.models.resolve()}:{MODEL_DIR_WITHIN_CONTAINER}",
        f"-e LOG_LEVEL={log_level}",
        f"-e PERCEPTION_MODEL_FILE={MODEL_DIR_WITHIN_CONTAINER}/{paths.perception_model.name}",
        "-e PERCEPTION_CONFIG_FILE=src/emma_perception/constants/vinvl_x152c4_alfred.yaml",
        "-e ONLY_PERCEPTION=1",
        f"--mount type=bind,source={Path.cwd()}/src/emma_experience_hub/entrypoints/run-teach-api.sh,target=/app/run-teach-api.sh",
        '--entrypoint "/bin/bash"',
        "-t heriot-watt/emma-simbot:full",
        "/app/run-teach-api.sh",
    ]

    subprocess.run(" ".join(command), shell=True, check=True)


def launch_api(
    dataset_split: TEAChDatasetSplit = typer.Option(..., show_envvar=False),
    log_level: str = typer.Option(
        "debug", envvar="LOG_LEVEL", help="Log level for the Policy and Perception APIs"
    ),
    clear_output_dir: bool = typer.Option(
        default=False, help="Clear the output directory", show_envvar=False
    ),
    use_gpu: bool = typer.Option(
        default=is_cuda_available(), help="Run using GPU", show_envvar=False
    ),
    api_port: int = typer.Option(
        default=POLICY_API_DEFAULT_PORT,
        help="Exposed API port from the API container",
        show_envvar=False,
    ),
) -> None:
    """Run the TEACh API for EMMA."""
    # Stop the container if it is running already.
    stop_api()

    # Check whether the API is going to be running without a display
    should_run_without_display = (
        machine_supports_inference_without_display() and is_xserver_display_running()
    )
    if should_run_without_display:
        console.log(
            "Launch the API to function [b u]without a display[/]. If this is [b u]not desired[/] then verify that your machine supports running inference without a display and that the display is running."
        )
        create_network_if_not_exists(DOCKER_NETWORK_NAME)

    paths = TEAChPaths()
    paths.create_output_dir(clear_output_dir)

    command = [
        "docker",
        "run",
        "--rm",
        f"--name {API_CONTAINER_NAME}",
        f"--network {DOCKER_NETWORK_NAME}" if should_run_without_display else "",
        f"-p {api_port}:{POLICY_API_DEFAULT_PORT}",
        '--gpus "device=0"' if use_gpu else "",
        f"-v {paths.models.resolve()}:{MODEL_DIR_WITHIN_CONTAINER}",
        f"-v {paths.data.resolve()}:/data:ro",
        f"-v {paths.output_frames.resolve()}:/images:ro",
        f"-e SPLIT={dataset_split.value}",
        f"-e LOG_LEVEL={log_level}",
        f"-e PERCEPTION_MODEL_FILE={MODEL_DIR_WITHIN_CONTAINER}/{paths.perception_model.name}",
        f"-e POLICY_MODEL_FILE={MODEL_DIR_WITHIN_CONTAINER}/{paths.policy_model.name}",
        "-e PERCEPTION_CONFIG_FILE=src/emma_perception/constants/vinvl_x152c4_alfred.yaml",
        f"--mount type=bind,source={Path.cwd()}/src/emma_experience_hub/entrypoints/run-teach-api.sh,target=/app/run-teach-api.sh",
        '--entrypoint "/bin/bash"',
        "-t heriot-watt/emma-simbot:full",
        "/app/run-teach-api.sh",
    ]

    subprocess.run(" ".join(command), shell=True, check=True)


def stop_api() -> None:
    """Stop the container running the API."""
    return stop_container(API_CONTAINER_NAME)


def stop_feature_extractor_api() -> None:
    """Stop the container running the Feature Extractor API."""
    return stop_container(FEATURE_EXTRACTOR_CONTAINER_NAME)

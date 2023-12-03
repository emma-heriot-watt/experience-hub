"""Commands to run the Experience Hub for SimBot.

This module contains all the commands used to run the Experience Hub for the SimBot challenge.

This module has become a bit unruly and needs a refactor to simplify commands, make it clear what
is happening and how to do things, and make it more DRY.
"""

import os
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Literal, Optional, cast

import typer
import yaml
from loguru import logger
from rich.console import Console
from rich.syntax import Syntax

from emma_common.api.gunicorn import create_gunicorn_server
from emma_common.logging import InterceptHandler, setup_logging, setup_rich_logging
from emma_experience_hub.api.simbot import app as simbot_api
from emma_experience_hub.common.settings import SimBotSettings
from emma_experience_hub.constants.simbot import get_service_registry_file_path
from emma_experience_hub.datamodels import ServiceRegistry


MODEL_STORAGE_DIR = Path("storage/models/")

SERVICE_REGISTRY_PATH = get_service_registry_file_path()

SERVICES_COMPOSE_PATH = Path("docker/docker-compose.yaml")
OBSERVABILITY_OVERRIDES_COMPOSE_PATH = Path("docker/docker-compose.observability.yaml")
GPU_OVERRIDES_PATH_SWITCHER: Mapping[int, Path] = MappingProxyType(
    {
        1: Path("docker/docker-compose.1gpu.yaml"),
        2: Path("docker/docker-compose.2gpu.yaml"),
        3: Path("docker/docker-compose.3gpu.yaml"),
        4: Path("docker/docker-compose.4gpu.yaml"),
    }
)


def build_compose_file_options(
    *,
    enable_observability: bool = False,
    num_gpus: Optional[Literal[1, 2, 3, 4]] = None,
    enable_offline_evaluation: bool = False,
) -> str:
    """Build the Docker Compose command to run the services."""
    os.environ["ENABLE_OBSERVABILITY"] = str(enable_observability)

    service_registry = ServiceRegistry.parse_obj(
        yaml.safe_load(SERVICE_REGISTRY_PATH.read_bytes())
    )

    # Set env vars for the services
    service_registry.update_all_env_vars()

    compose_file_option = f"-f {SERVICES_COMPOSE_PATH}"

    if num_gpus is not None:
        compose_gpu_overrides = GPU_OVERRIDES_PATH_SWITCHER[num_gpus]
        compose_file_option = f"{compose_file_option} -f {compose_gpu_overrides}"

    if enable_observability:
        compose_file_option = f"{compose_file_option} -f {OBSERVABILITY_OVERRIDES_COMPOSE_PATH}"

    if not enable_offline_evaluation:
        compose_file_option = f"{compose_file_option} --profile not-offline-evaluation"

    return compose_file_option


app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    short_help="Setup and run the SimBot API.",
    help="Commands for setup and running inference on SimBot Arena.",
)


@app.command()
def print_compose_config(
    observability: bool = typer.Option(
        False,  # noqa: WPS425
        "--observability",
        is_flag=True,
        help="Run the services with observability enabled.",
    ),
    num_gpus: Optional[int] = typer.Option(
        None, min=1, max=4, help="Run the services with the specified number of GPUs."
    ),
    offline_evaluation: bool = typer.Option(
        False,  # noqa: WPS425
        "--offline-evaluation",
        is_flag=True,
        help="Run the services with offline evaluation enabled.",
    ),
) -> None:
    """Print the config for the docker compose."""
    compose_file_options = build_compose_file_options(
        enable_observability=observability,
        num_gpus=cast(Optional[Literal[1, 2, 3, 4]], num_gpus),
        enable_offline_evaluation=offline_evaluation,
    )
    # Run services
    command_output = subprocess.run(
        f"docker compose {compose_file_options} config",
        shell=True,
        check=True,
        capture_output=True,
    )

    Console().print(
        Syntax(
            command_output.stdout.decode("utf-8"),
            "yaml",
            theme="ansi_dark",
        )
    )


@app.command()
def pull_service_images() -> None:
    """Pull images for the various services."""
    compose_file_options = build_compose_file_options(enable_observability=True, num_gpus=None)

    # Pull service images
    subprocess.run(
        f"docker compose {compose_file_options} pull",
        shell=True,
        check=True,
    )


@app.command(name="download-models")
def download_model_checkpoints(
    model_storage_dir: Path = typer.Option(
        default=MODEL_STORAGE_DIR, help="Directory to save models.", rich_help_panel="Models"
    ),
    force_download_models: bool = typer.Option(
        False,  # noqa: WPS425
        "--force",
        "-f",
        is_flag=True,
        help="Force download all models for all services.",
        rich_help_panel="Models",
    ),
) -> None:
    """Download the model checkpoints."""
    # Load the registry for the services
    service_registry = ServiceRegistry.parse_obj(
        yaml.safe_load(SERVICE_REGISTRY_PATH.read_bytes())
    )
    service_registry.update_all_env_vars()

    # Create model storage dir
    model_storage_dir.mkdir(exist_ok=True, parents=True)

    # Download models
    service_registry.download_all_models(model_storage_dir, force=force_download_models)


@app.command()
def run_background_services(
    model_storage_dir: Path = typer.Option(
        default=MODEL_STORAGE_DIR, help="Directory to save models.", rich_help_panel="Models"
    ),
    force_download_models: bool = typer.Option(
        False,  # noqa: WPS425
        "--force",
        "-f",
        is_flag=False,
        help="Force download models for all services.",
        rich_help_panel="Models",
    ),
    run_in_background: bool = typer.Option(
        False,  # noqa: WPS425
        "--run-in-background",
        "-d",
        is_flag=True,
        help="Run the services in the background.",
    ),
    observability: bool = typer.Option(
        False,  # noqa: WPS425
        "--observability",
        is_flag=True,
        help="Run the services with observability enabled.",
    ),
    num_gpus: Optional[int] = typer.Option(
        None, min=1, max=4, help="Run the services with the specified number of GPUs."
    ),
    offline_evaluation: bool = typer.Option(
        False,  # noqa: WPS425
        "--offline-evaluation",
        is_flag=True,
        help="Run the services with offline evaluation enabled.",
    ),
) -> None:
    """Run all the services for SimBot inference."""
    # Download the models if need be
    download_model_checkpoints(model_storage_dir, force_download_models)

    # Get the files to use for the run command
    compose_file_options = build_compose_file_options(
        enable_observability=observability,
        num_gpus=cast(Optional[Literal[1, 2, 3, 4]], num_gpus),
        enable_offline_evaluation=offline_evaluation,
    )

    # Build the run command
    run_command = "up"
    if run_in_background:
        run_command = f"{run_command} -d"

    # Run services
    subprocess.run(f"docker compose {compose_file_options} {run_command}", shell=True, check=True)


@app.command()
def run_controller_api(
    auxiliary_metadata_dir: Path = typer.Option(
        ...,
        help="Local directory to source metadata from the Arena.",
        rich_help_panel="Directories",
    ),
    auxiliary_metadata_cache_dir: Path = typer.Option(
        ...,
        help="Local directory to store the cached auxiliary metadata.",
        writable=True,
        exists=True,
        rich_help_panel="Directories",
    ),
    extracted_features_cache_dir: Path = typer.Option(
        ...,
        help="Local directory to store cache the extracted features in.",
        writable=True,
        exists=True,
        rich_help_panel="Directories",
    ),
    observability: bool = typer.Option(
        False,  # noqa: WPS425
        "--observability",
        is_flag=True,
        help="Run the services with observability enabled.",
    ),
    workers: int = typer.Option(
        default=1, min=1, help="Set the number of workers to run the server with."
    ),
    timeout: int = typer.Option(
        default=100, min=10, help="Set the number of seconds until the timeout."
    ),
) -> None:
    """Run the inference server."""
    os.environ["SIMBOT_AUXILIARY_METADATA_DIR"] = str(auxiliary_metadata_dir)
    os.environ["SIMBOT_AUXILIARY_METADATA_CACHE_DIR"] = str(auxiliary_metadata_cache_dir)
    os.environ["SIMBOT_EXTRACTED_FEATURES_CACHE_DIR"] = str(extracted_features_cache_dir)

    # Do not track any healthcheck calls
    os.environ["OTEL_PYTHON_EXCLUDED_URLS"] = "healthcheck,ping"

    simbot_settings = SimBotSettings.from_env()

    if observability:
        setup_logging(sys.stdout, InterceptHandler())
    else:
        setup_rich_logging(rich_traceback_show_locals=False)

    server = create_gunicorn_server(
        simbot_api,
        simbot_settings.host,
        simbot_settings.port,
        workers,
        timeout=timeout,
    )

    server.run()


@app.command()
def run_production_server(
    workers: int = typer.Option(
        default=4, min=1, help="Set the number of workers when running in production."
    )
) -> None:
    """Run all the services in the background and start the server.

    This command should only be run on the EC2 instance, where the relevant EFS directories have
    already been setup.
    """
    logger.warning(
        "This command will likely only work properly on the production EC2 instance AMI. This is because it directly refers to paths according to how the AMI has been set-up. If you are running on the EC2 instance, you can ignore this warning."
    )

    run_background_services(
        model_storage_dir=MODEL_STORAGE_DIR,
        force_download_models=False,
        run_in_background=True,
        observability=True,
        num_gpus=4,
        offline_evaluation=False,
    )
    run_controller_api(
        auxiliary_metadata_dir=Path("../auxiliary_metadata"),
        auxiliary_metadata_cache_dir=Path("../cache/auxiliary_metadata"),
        extracted_features_cache_dir=Path("../cache/features"),
        observability=True,
        workers=workers,
        timeout=100,
    )


if __name__ == "__main__":
    app()

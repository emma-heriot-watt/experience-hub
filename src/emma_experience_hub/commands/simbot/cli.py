"""Commands to run the Experience Hub for SimBot.

This module contains all the commands used to run the Experience Hub for the SimBot challenge.

This module has become a bit unruly and needs a refactor to simplify commands, make it clear what
is happening and how to do things, and make it more DRY.
"""

import os
import subprocess
import sys
from pathlib import Path

import typer
import yaml
from loguru import logger
from rich.console import Console
from rich.syntax import Syntax

from emma_common.api.gunicorn import create_gunicorn_server
from emma_common.api.instrumentation import instrument_app
from emma_common.logging import InstrumentedInterceptHandler, setup_logging, setup_rich_logging
from emma_experience_hub._version import __version__  # noqa: WPS436
from emma_experience_hub.api.observability import send_logs_to_cloudwatch
from emma_experience_hub.api.simbot import app as simbot_api
from emma_experience_hub.common.settings import SimBotSettings
from emma_experience_hub.datamodels import ServiceRegistry


MODEL_STORAGE_DIR = Path("storage/models/")

SERVICE_REGISTRY_PATH = Path("storage/registry/simbot/production.yaml")

SERVICES_COMPOSE_PATH = Path("docker/simbot-docker-compose.yaml")
SERVICES_STAGING_COMPOSE_PATH = Path("docker/simbot-docker-compose.staging.yaml")
SERVICES_PROD_COMPOSE_PATH = Path("docker/simbot-docker-compose.prod.yaml")

OBSERVABILITY_COMPOSE_PATH = Path("docker/observability-docker-compose.yaml")

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    short_help="Setup and run the SimBot API.",
    help="Commands for setup and running inference on SimBot Arena.",
)


@app.command()
def print_compose_config(
    enable_observability: bool = typer.Option(
        default=False, is_flag=True, help="Run the services with observability enabled."
    ),
    is_production: bool = typer.Option(
        False,  # noqa: WPS425
        "--production",
        is_flag=True,
        help="Run the background services using the production config",
    ),
) -> None:
    """Print the config for the docker compose."""
    os.environ["ENABLE_OBSERVABILITY"] = str(enable_observability)

    service_registry = ServiceRegistry.parse_obj(
        yaml.safe_load(SERVICE_REGISTRY_PATH.read_bytes())
    )

    # Set env vars for the services
    service_registry.update_all_env_vars()

    compose_file_option = f"-f {SERVICES_COMPOSE_PATH}"
    if is_production:
        compose_file_option = f"{compose_file_option} -f {SERVICES_PROD_COMPOSE_PATH}"
    else:
        compose_file_option = f"{compose_file_option} -f {SERVICES_STAGING_COMPOSE_PATH}"

    if enable_observability:
        compose_file_option = f"{compose_file_option} -f {OBSERVABILITY_COMPOSE_PATH}"

    # Run services
    command_output = subprocess.run(
        f"docker compose {compose_file_option} config", shell=True, check=True, capture_output=True
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
    # Load the registry for the services
    service_registry = ServiceRegistry.parse_obj(
        yaml.safe_load(SERVICE_REGISTRY_PATH.read_bytes())
    )

    # Set env vars for the services
    service_registry.update_all_env_vars()

    # Pull service images
    subprocess.run(
        f"docker compose -f {SERVICES_COMPOSE_PATH} -f {OBSERVABILITY_COMPOSE_PATH} pull",
        shell=True,
        check=True,
    )


@app.command()
def run_background_services(
    service_registry_path: Path = typer.Option(
        default=SERVICE_REGISTRY_PATH,
        help="Location of the services registry",
        rich_help_panel="Config",
    ),
    services_docker_compose_path: Path = typer.Option(
        default=SERVICES_COMPOSE_PATH,
        help="Docker Compose configuration for the background services.",
        rich_help_panel="Config",
    ),
    staging_services_docker_compose_path: Path = typer.Option(
        default=SERVICES_STAGING_COMPOSE_PATH,
        help="Addiional configuration for the staging environment.",
        rich_help_panel="Config",
    ),
    production_services_docker_compose_path: Path = typer.Option(
        SERVICES_PROD_COMPOSE_PATH,
        help="Additional configuration for the production environment.",
        rich_help_panel="Config",
    ),
    observability_services_docker_compose_path: Path = typer.Option(
        OBSERVABILITY_COMPOSE_PATH,
        help="Observability services for the SimBot environment",
        rich_help_panel="Config",
    ),
    model_storage_dir: Path = typer.Option(
        default=MODEL_STORAGE_DIR, help="Directory to save models.", rich_help_panel="Models"
    ),
    download_models: bool = typer.Option(
        default=True,
        help="Download all models for the services if necessary.",
        rich_help_panel="Models",
    ),
    force_download: bool = typer.Option(
        False,  # noqa: WPS425
        "--force",
        "-f",
        is_flag=True,
        help="Force download all models for all services.",
        rich_help_panel="Models",
    ),
    run_in_background: bool = typer.Option(
        False,  # noqa: WPS425
        "--run-in-background",
        "-d",
        is_flag=True,
        help="Run the services in the background.",
    ),
    enable_observability: bool = typer.Option(
        default=False, is_flag=True, help="Run the services with observability enabled."
    ),
    is_production: bool = typer.Option(
        False,  # noqa: WPS425
        "--production",
        is_flag=True,
        help="Run the background services using the production config",
    ),
) -> None:
    """Run all the services for SimBot inference."""
    os.environ["ENABLE_OBSERVABILITY"] = str(enable_observability)

    # Load the registry for the services
    service_registry = ServiceRegistry.parse_obj(
        yaml.safe_load(service_registry_path.read_bytes())
    )

    # Set env vars for the services
    service_registry.update_all_env_vars()

    if download_models:
        # Create model storage dir
        model_storage_dir.mkdir(exist_ok=True, parents=True)

        # Download models
        service_registry.download_all_models(model_storage_dir, force=force_download)

    # Build the run command
    run_command = "up"
    if run_in_background:
        run_command = f"{run_command} -d"

    compose_file_option = f"-f {services_docker_compose_path}"
    if is_production:
        compose_file_option = f"{compose_file_option} -f {production_services_docker_compose_path}"
    else:
        compose_file_option = f"{compose_file_option} -f {staging_services_docker_compose_path}"

    if enable_observability:
        compose_file_option = (
            f"{compose_file_option} -f {observability_services_docker_compose_path}"
        )

    # Run services
    subprocess.run(f"docker compose {compose_file_option} {run_command}", shell=True, check=True)


@app.command()
def run_controller_api(
    auxiliary_metadata_dir: Path = typer.Option(
        ...,
        help="Local directory to source metadata from the Arena.",
        rich_help_panel="Directories",
    ),
    auxiliary_metadata_cache_dir: Path = typer.Option(
        ...,
        help="Local directory to store the cached auxiliary metadata before uploading to S3.",
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
    log_to_cloudwatch: bool = typer.Option(
        default=False,
        help="Send logs to CloudWatch",
        rich_help_panel="Observability",
    ),
    traces_to_opensearch: bool = typer.Option(
        default=False,
        help="Send trace information to OpenSearch to track metrics and requests.",
        rich_help_panel="Observability",
    ),
    workers: int = typer.Option(
        default=1, min=1, help="Set the number of workers to run the server with."
    ),
) -> None:
    """Run the inference server."""
    os.environ["SIMBOT_AUXILIARY_METADATA_DIR"] = str(auxiliary_metadata_dir)
    os.environ["SIMBOT_AUXILIARY_METADATA_CACHE_DIR"] = str(auxiliary_metadata_cache_dir)
    os.environ["SIMBOT_EXTRACTED_FEATURES_CACHE_DIR"] = str(extracted_features_cache_dir)

    # Do not track any healthcheck calls
    os.environ["OTEL_PYTHON_EXCLUDED_URLS"] = "healthcheck,ping"

    simbot_settings = SimBotSettings.from_env()

    if traces_to_opensearch:
        instrument_app(
            simbot_api,
            otlp_endpoint=simbot_settings.otlp_endpoint,
            service_name=simbot_settings.opensearch_service_name,
            service_version=__version__,
            service_namespace="SimBot",
        )
        setup_logging(sys.stdout, InstrumentedInterceptHandler())
    else:
        setup_rich_logging(rich_traceback_show_locals=False)

    server = create_gunicorn_server(
        simbot_api, simbot_settings.host, simbot_settings.port, workers
    )

    if log_to_cloudwatch:
        send_logs_to_cloudwatch(simbot_settings, traces_to_opensearch)

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
        download_models=True,
        run_in_background=True,
        enable_observability=True,
        is_production=True,
    )
    run_controller_api(
        auxiliary_metadata_dir=Path("../auxiliary_metadata"),
        auxiliary_metadata_cache_dir=Path("../cache/auxiliary_metadata"),
        extracted_features_cache_dir=Path("../cache/features"),
        log_to_cloudwatch=True,
        traces_to_opensearch=True,
        workers=workers,
    )


if __name__ == "__main__":
    app()

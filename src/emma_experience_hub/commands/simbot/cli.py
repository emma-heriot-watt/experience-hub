import os
import subprocess
import sys
from pathlib import Path

import typer
import yaml
from loguru import logger

from emma_common.api.gunicorn import create_gunicorn_server
from emma_common.api.instrumentation import InstrumentedInterceptHandler
from emma_common.logging import setup_logging, setup_rich_logging
from emma_experience_hub.api.observability import instrument_app, send_logs_to_cloudwatch
from emma_experience_hub.api.simbot import app as simbot_api
from emma_experience_hub.common.settings import SimBotSettings
from emma_experience_hub.datamodels import ServiceRegistry


app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    short_help="Setup and run the SimBot API.",
    help="Commands for setup and running inference on SimBot Arena.",
)


@app.command()
def run_background_services(
    registry_path: Path = typer.Option(
        Path("storage/registry/simbot/production.yaml"),
        help="Location of the registry .yaml file",
        exists=True,
        file_okay=True,
    ),
    compose_file_path: Path = typer.Option(
        Path("docker/simbot-docker-compose.yaml"),
        help="Location of the compose definition file.",
        exists=True,
        file_okay=True,
    ),
    download_models: bool = typer.Option(
        default=True, help="Download all models for the services if necessary."
    ),
    force_download: bool = typer.Option(
        False,  # noqa: WPS425
        "--force",
        "-f",
        is_flag=True,
        help="Force download all models for all services.",
    ),
    run_in_background: bool = typer.Option(
        False,  # noqa: WPS425
        "--run-in-background",
        "-d",
        is_flag=True,
        help="Run the services in the background.",
    ),
) -> None:
    """Run all the services for SimBot inference."""
    # Load the registry for the services
    service_registry = ServiceRegistry.parse_obj(yaml.safe_load(registry_path.read_bytes()))

    # Set env vars for the services
    service_registry.update_all_env_vars()

    if download_models:
        # Create model storage dir
        model_storage_dir = Path("storage/models/")
        model_storage_dir.mkdir(exist_ok=True, parents=True)

        # Download models
        service_registry.download_all_models(model_storage_dir, force=force_download)

    # Build the run command
    run_command = "up"
    if run_in_background:
        run_command = f"{run_command} -d"

    # Run services
    subprocess.run(f"docker compose -f {compose_file_path} {run_command}", shell=True, check=True)


@app.command()
def run_observability_services(
    compose_file_path: Path = typer.Option(
        Path("docker/observability-docker-compose.yaml"),
        help="Location of the compose definition file.",
        exists=True,
        file_okay=True,
    ),
    run_in_background: bool = typer.Option(
        False,  # noqa: WPS425
        "--run-in-background",
        "-d",
        is_flag=True,
        help="Run the services in the background.",
    ),
) -> None:
    """Run the additional observability services."""
    run_command = "up"
    if run_in_background:
        run_command = f"{run_command} -d"

    # Run services
    subprocess.run(f"docker compose -f {compose_file_path} {run_command}", shell=True, check=True)


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

    simbot_settings = SimBotSettings.from_env()

    if traces_to_opensearch:
        instrument_app(simbot_api, simbot_settings)
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
        registry_path=Path("storage/registry/simbot/production.yaml"),
        compose_file_path=Path("docker/simbot-docker-compose.yaml"),
        download_models=True,
        run_in_background=True,
    )
    run_observability_services(
        compose_file_path=Path("docker/observability-docker-compose.yaml"), run_in_background=True
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

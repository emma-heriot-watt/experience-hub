import os
import subprocess
from pathlib import Path

import typer
from rich.console import Console
from rich.syntax import Syntax

from emma_common.api.gunicorn import create_gunicorn_server
from emma_common.logging import setup_rich_logging
from emma_experience_hub.api.simbot import app as simbot_api
from emma_experience_hub.common.settings import SimBotSettings


SERVICES_COMPOSE_PATH = Path("docker/docker-compose.yaml")
GPU_OVERRIDES_PATH = Path("docker/docker-compose.1gpu.yaml")


def build_compose_file_options(*, with_gpu: bool = False) -> str:
    """Build the Docker Compose command to run the services."""
    compose_file_option = f"-f {SERVICES_COMPOSE_PATH}"
    if with_gpu:
        compose_file_option = f"{compose_file_option} -f {GPU_OVERRIDES_PATH}"

    return compose_file_option


app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    short_help="Setup and run the API.",
    help="Commands for setup and running inference on Alexa Arena.",
)


@app.command()
def print_compose_config(
    with_gpu: bool = typer.Option(
        False,  # noqa: WPS425
        "--gpu",
        "--with-gpu",
        is_flag=True,
        help="Run the services on the GPU.",
    ),
) -> None:
    """Print the config for the docker compose."""
    compose_file_options = build_compose_file_options(with_gpu=with_gpu)
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
def run_background_services(
    run_in_background: bool = typer.Option(
        False,  # noqa: WPS425
        "--run-in-background",
        "-d",
        is_flag=True,
        help="Run the services in the background.",
    ),
    with_gpu: bool = typer.Option(
        False,  # noqa: WPS425
        "--gpu",
        "--with-gpu",
        is_flag=True,
        help="Run the services on the GPU.",
    ),
) -> None:
    """Run all the services for SimBot inference."""
    # Get the files to use for the run command
    compose_file_options = build_compose_file_options(with_gpu=with_gpu)

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

    simbot_settings = SimBotSettings.from_env()

    setup_rich_logging(rich_traceback_show_locals=False)

    server = create_gunicorn_server(
        simbot_api,
        simbot_settings.host,
        simbot_settings.port,
        workers,
        timeout=timeout,
    )
    server.run()


if __name__ == "__main__":
    app()

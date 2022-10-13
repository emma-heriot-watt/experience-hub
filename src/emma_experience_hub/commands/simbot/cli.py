import os
from pathlib import Path

import typer
from loguru import logger
from uvicorn import Config, Server

from emma_experience_hub.common.logging import setup_logging
from emma_experience_hub.common.settings import SimBotSettings


app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    short_help="Setup and run the SimBot API.",
    help="Commands for setup and running inference on SimBot Arena.",
)


@app.command()
def run_inference_server(
    auxiliary_metadata_dir: str = typer.Option(
        ...,
        help="Local directory to source metadata from the Arena.",
    ),
    auxiliary_metadata_cache_dir: Path = typer.Option(
        ...,
        help="Local directory to store the cached auxiliary metadata before uploading to S3.",
        writable=True,
        exists=True,
    ),
    extracted_features_dir: Path = typer.Option(
        ...,
        help="Local directory to store cache the extracted features in.",
        writable=True,
        exists=True,
    ),
    log_to_cloudwatch: bool = typer.Option(default=False, help="Send logs to CloudWatch"),
) -> None:
    """Run the inference server."""
    os.environ["SIMBOT_AUXILIARY_METADATA_CACHE_DIR"] = str(auxiliary_metadata_cache_dir)
    os.environ["SIMBOT_AUXILIARY_METADATA_DIR"] = str(auxiliary_metadata_dir)
    os.environ["SIMBOT_EXTRACTED_FEATURES_DIR"] = str(extracted_features_dir)

    simbot_settings = SimBotSettings.from_env()

    server = Server(
        Config(
            "emma_experience_hub.api.controllers.simbot:app",
            host=simbot_settings.host,
            port=simbot_settings.port,
        ),
    )

    setup_logging()

    if log_to_cloudwatch:
        try:
            import watchtower  # noqa: WPS433

            logger.add(
                watchtower.CloudWatchLogHandler(
                    log_group_name=simbot_settings.watchtower_log_group_name,
                    log_stream_name=simbot_settings.watchtower_log_stream_name,
                )
            )
        except ModuleNotFoundError:
            logger.warning(
                "Watchtower package not found. Ensure you have installed the package with `poetry install --with production`."
            )

    server.run()


if __name__ == "__main__":
    app()

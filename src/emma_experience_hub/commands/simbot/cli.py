from pathlib import Path

import typer


app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    short_help="Setup and run the SimBot API.",
    help="Simplified commands for setup and running infernece on SimBot Arena.",
)


@app.command()
def run_inference_server(
    aws_profile: str = typer.Option("TeamProfile", help="Name of the AWS profile to use."),
    auxiliary_metadata_s3_bucket: str = typer.Option(
        ...,
        help="S3 bucket to store the auxiliary metadata from the arena.",
        rich_help_panel="Auxiliary Metadata",
    ),
    auxiliary_metadata_dir: Path = typer.Option(
        ...,
        help="Local directory to store the auxiliary metadata before uploading to S3.",
        rich_help_panel="Auxiliary Metadata",
        writable=True,
        exists=True,
    ),
    session_db_memory_table_name: str = typer.Option(
        "MEMORY_TABLE",
        help="Table name within the DynamoDB to store SimBot session data",
        rich_help_panel="Session DB",
    ),
    session_db_region: str = typer.Option(
        "us-east-1",
        help="AWS region for the DynamoDB instance.",
        rich_help_panel="Session DB",
    ),
    perception_root: Path = typer.Option(
        ...,
        help="Directory of the perception repository",
        exists=True,
        rich_help_panel="EMMA Repositories",
    ),
    perception_python_executable: Path = typer.Option(
        ...,
        help="Location of the python virtualenv executable for Perception. This will need to have all the dependencies installed for the project.",
        rich_help_panel="EMMA Repositories",
        exists=True,
    ),
    policy_root: Path = typer.Option(
        ...,
        help="Directory of the perception repository",
        exists=True,
        rich_help_panel="EMMA Repositories",
    ),
    policy_python_executable: Path = typer.Option(
        ...,
        help="Location of the python virtualenv executable for Policy. This will need to have all the dependencies installed for the project.",
        rich_help_panel="EMMA Repositories",
        exists=True,
    ),
    feature_extractor_url: str = typer.Option(
        "http://0.0.0.0:5500",
        help="URL for the feature extractor service",
        rich_help_panel="EMMA Services",
    ),
    nlu_predictor_url: str = typer.Option(
        "http://0.0.0.0:5501",
        help="URL for the NLU predictor service",
        rich_help_panel="EMMA Services",
    ),
    interaction_action_predictor_url: str = typer.Option(
        "http://0.0.0.0:5502",
        help="URL for the interaction action prediction service",
        rich_help_panel="EMMA Services",
    ),
) -> None:
    """Run the inference server."""
    raise NotImplementedError


if __name__ == "__main__":
    app()

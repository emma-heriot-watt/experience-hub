from typing import Optional

import typer

from emma_experience_hub.commands.build_emma import build_emma_images, torch_cuda_version_callback
from emma_experience_hub.commands.teach import app as teach_cli
from emma_experience_hub.common import load_env_vars


load_env_vars()

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Commands you might need to setup your environment for EMMA, and run EMMA.",
)


@app.command()
def build_emma(
    torch_cuda_version: Optional[str] = typer.Option(
        None,
        callback=torch_cuda_version_callback,
        help="Optionally, provide the specific CUDA version you want to install within the container. Defaults to using the best for the current machine.",
    )
) -> None:
    """Build the Docker images for EMMA (not including any model checkpoint).

    The CUDA version of the machine is checked to ensure the correct torch-CUDA version is
    installed.
    """
    return build_emma_images(torch_cuda_version)


app.add_typer(teach_cli, name="teach")

if __name__ == "__main__":
    app()

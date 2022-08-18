import subprocess
from typing import Optional

import typer

from emma_experience_hub.commands.torch import (
    get_supported_cuda_version,
    get_torch_cuda_suffix,
    is_cuda_available,
)


def get_torch_version_suffix() -> str:
    """Get the torch CUDA version that best supports the current machine."""
    if not is_cuda_available():
        return ""

    supported_cuda_version = get_supported_cuda_version()
    torch_suffix = get_torch_cuda_suffix(supported_cuda_version)

    if torch_suffix:
        torch_suffix = f"+{torch_suffix}"

    return torch_suffix


app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    short_help="Run various Docker commands.",
    help="Easily run the various Docker-related commands for doing things.",
)


@app.callback()
def callback() -> None:
    """Empty callback to ensure that each command function is separate.

    https://typer.tiangolo.com/tutorial/commands/one-or-multiple/#one-command-and-one-callback
    """
    pass  # noqa: WPS420


def torch_cuda_version_callback(torch_version: Optional[str]) -> str:
    """Validate the provided torch CUDA version."""
    if not torch_version:
        return ""

    if not torch_version.startswith("cu"):
        raise typer.BadParameter("The suffix must start with `cu`")

    try:
        int(torch_version.split("cu")[-1])
    except ValueError:
        raise typer.BadParameter(
            "The cuda version must be castable to an integer. For example, `113` and not `11.3`"
        )

    return torch_version


@app.command()
def build(
    torch_cuda_version: Optional[str] = typer.Option(None, callback=torch_cuda_version_callback)
) -> None:
    """Build all the docker images for EMMA."""
    # TODO: Verify docker is installed
    # TODO: Verify docker buildx is available (check version >= x?)

    torch_cuda_version = torch_cuda_version if torch_cuda_version else get_torch_version_suffix()

    subprocess.run("docker buildx use default", shell=True, check=True)

    images_to_build = [
        "base",
        "base-poetry",
        "emma-perception",
        "emma-policy",
        "emma-full",
    ]

    for image_target in images_to_build:
        subprocess.run(
            f"docker buildx bake -f docker/docker-bake.hcl --set '*.args.TORCH_VERSION_SUFFIX={torch_cuda_version}' {image_target}",
            shell=True,
            check=True,
        )


if __name__ == "__main__":
    app()

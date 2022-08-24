import subprocess
from typing import Optional

import typer

from emma_experience_hub.common.torch import get_torch_version_suffix


def torch_cuda_version_callback(torch_version: Optional[str]) -> str:
    """Validate the provided torch CUDA version."""
    if not torch_version:
        return ""

    if not torch_version.startswith("+cu"):
        raise typer.BadParameter("The suffix must start with `+cu`")

    try:
        int(torch_version.split("+cu")[-1])
    except ValueError:
        raise typer.BadParameter(
            "The cuda version must be castable to an integer. For example, `113` and not `11.3`"
        )

    return torch_version


def build_emma_images(torch_cuda_version: Optional[str]) -> None:
    """Build all the docker images for EMMA."""
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

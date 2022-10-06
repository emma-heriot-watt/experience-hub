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


def build_emma(
    torch_cuda_version: Optional[str] = typer.Option(
        None,
        callback=torch_cuda_version_callback,
        help="Optionally, provide the specific CUDA version you want to install within the container. Defaults to using the best for the current machine.",
    ),
    perception_remote_branch_name: str = typer.Option(
        default="main",
        help="Optionally, specify the name of the branch from the Perception repository to clone",
        rich_help_panel="Repository Options",
    ),
    policy_remote_branch_name: str = typer.Option(
        default="main",
        help="Optionally, specify the name of the branch from the Policy repository to clone",
        rich_help_panel="Repository Options",
    ),
) -> None:
    """Build the Docker images for EMMA (not including any model checkpoint).

    The CUDA version of the machine is checked to ensure the correct torch-CUDA version is
    installed.
    """
    torch_cuda_version = torch_cuda_version if torch_cuda_version else get_torch_version_suffix()

    subprocess.run("docker buildx use default", shell=True, check=True)

    images_to_build = [
        "base",
        "base-poetry",
        "emma-perception",
        "emma-policy",
        # "emma-full",
    ]

    for image_target in images_to_build:
        command: list[str] = [
            "docker buildx bake",
            "-f docker/docker-bake.hcl",
            f"--set '*.args.TORCH_VERSION_SUFFIX={torch_cuda_version}'",
            f"--set 'emma-perception*.args.REMOTE_REPO_BRANCH={perception_remote_branch_name}'",
            f"--set 'emma-policy*.args.REMOTE_REPO_BRANCH={policy_remote_branch_name}'",
            image_target,
        ]

        subprocess.run(" ".join(command), shell=True, check=True)

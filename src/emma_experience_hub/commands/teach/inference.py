import subprocess
from shutil import rmtree
from typing import Optional
from venv import create as create_virtualenv

import typer
from rich.console import Console

from emma_experience_hub.commands.teach.constants import (
    API_CONTAINER_NAME,
    DOCKER_NETWORK_NAME,
    INFERENCE_RUNNER_CONTAINER_NAME,
    INFERENCE_RUNNER_IMAGE_NAME,
    POLICY_API_DEFAULT_PORT,
    TEAChDatasetSplit,
    TEAChPaths,
)
from emma_experience_hub.commands.teach.dataset import (
    limit_edh_instances_evaluated,
    restore_unselected_edh_instances,
)
from emma_experience_hub.common.docker import (
    create_network_if_not_exists,
    is_container_running,
    stop_container,
)
from emma_experience_hub.common.system import (
    get_active_display_index,
    machine_supports_inference_without_display,
)
from emma_experience_hub.common.torch import is_cuda_available


console = Console()


def prepare_inference_runner_without_display() -> None:
    """Build the TEACh Inference Runner Docker image to run inference without a display."""
    subprocess.run("docker buildx use default", shell=True, check=True)
    subprocess.run(
        "docker buildx bake -f docker/docker-bake.hcl teach-inference", shell=True, check=True
    )


def prepare_inference_runner_with_display(force_reset: bool = False) -> None:
    """Prepare to run the inference runner with a display.

    This clones the `alexa/teach` repo locally, creates a virtualenv and installs the dependencies
    within it, keeping it isolated from the remainder of the package.
    """
    # Clean up if `force_reset` is true
    if force_reset and TEAChPaths.alexa_teach_repo.exists():
        rmtree(TEAChPaths.alexa_teach_repo.resolve())

    # Clone the `alexa/teach` repository
    if not TEAChPaths.alexa_teach_repo.exists():
        subprocess.run(
            f"git clone https://github.com/alexa/teach.git {TEAChPaths.alexa_teach_repo.resolve()}",
            shell=True,
            check=True,
        )

    # Create a new virtualenv for running TEACh
    if not TEAChPaths.alexa_teach_repo_venv.exists():
        create_virtualenv(TEAChPaths.alexa_teach_repo_venv.resolve(), with_pip=True)

    # Install the dependencies
    subprocess.run(
        f"{TEAChPaths.alexa_teach_repo_python.resolve()} -m pip install -r {TEAChPaths.alexa_teach_repo.joinpath('requirements.txt')}",
        shell=True,
        check=True,
    )
    # Install the alexa teach repo to its own venv
    subprocess.run(
        f"{TEAChPaths.alexa_teach_repo_python.resolve()} -m pip install -e {TEAChPaths.alexa_teach_repo.resolve()}",
        shell=True,
        check=True,
    )


def launch_inference_runner_with_display(
    dataset_split: TEAChDatasetSplit, clear_output_dir: bool = False
) -> None:
    """Run the TEACh EDH inference runner locally, without Docker."""
    paths = TEAChPaths()
    paths.create_output_dir(clear_output_dir)

    command = [
        f"{TEAChPaths.alexa_teach_repo_python} -m teach_inference",
        f"--data_dir {paths.data.resolve()}",
        f"--output_dir {paths.output_metadata.resolve()}",
        f"--images_dir {paths.output_frames.resolve()}",
        f"--split {dataset_split.value}",
        f"--metrics_file {paths.output_metadata.resolve()}/metrics",
        "--model_module teach.inference.remote_model",
        "--model_class RemoteModel",
        f"--model_api_host_and_port localhost:{POLICY_API_DEFAULT_PORT}",
    ]

    subprocess.run(" ".join(command), shell=True, check=True)


def launch_inference_runner_without_display(
    dataset_split: TEAChDatasetSplit, clear_output_dir: bool = False
) -> None:
    """Launch the inference runner for TEACh using Docker.

    You need to ensure that the X Server is running before running this.
    """
    if not machine_supports_inference_without_display():
        raise typer.Abort(
            "Your machine does not support using the inference runner without a display."
        )

    # Stop the container if it is running already.
    stop_inference_runner_container()
    create_network_if_not_exists(DOCKER_NETWORK_NAME)

    # Verify that the inference runner is running
    if not is_container_running(API_CONTAINER_NAME):
        raise AssertionError(
            "The TEACh API is not already running. Run `python -m emma_experience_hub teach launch_api` before running this command."
        )

    if not is_cuda_available():
        raise AssertionError(
            "This command only supports running the inference runner on a machine without a display (i.e. Linux with an NVIDIA GPU)"
        )

    paths = TEAChPaths()
    paths.create_output_dir(clear_output_dir)

    command = [
        "docker",
        "run",
        "--rm",
        "--privileged",
        f"--name {INFERENCE_RUNNER_CONTAINER_NAME}",
        f"--network {DOCKER_NETWORK_NAME}",
        f"-e DISPLAY=:{get_active_display_index()}",
        "-e NVIDIA_DRIVER_CAPABILITIES=all",
        '--gpus "device=0"',
        "-v /tmp/.X11-unix:/tmp/.X11-unix:ro",
        f"-v {paths.data.resolve()}:/data:ro",
        f"-v {paths.output_frames.resolve()}:/images",
        f"-v {paths.output_metadata.resolve()}:/output",
        # Run CMD
        f"{INFERENCE_RUNNER_IMAGE_NAME} teach_inference",
        "--data_dir /data",
        "--output_dir /output",
        "--images_dir /images",
        f"--split {dataset_split.value}",
        "--metrics_file /output/metrics",
        "--model_module teach.inference.remote_model",
        "--model_class RemoteModel",
        f"--model_api_host_and_port {API_CONTAINER_NAME}:{POLICY_API_DEFAULT_PORT}",
    ]

    subprocess.run(" ".join(command), shell=True, check=True)


def prepare_inference_runner(
    with_display: bool = typer.Option(
        ... if machine_supports_inference_without_display() else True,
        help="Whether or not inference will be run with or without a display",
        hidden=not machine_supports_inference_without_display(),
    ),
    force_reset: bool = typer.Option(
        default=False, help="Force reset the prepared inference runner and set it up again"
    ),
) -> None:
    """Prepare the inference runner for TEACh EDH instances."""
    if not with_display and not machine_supports_inference_without_display():
        raise typer.BadParameter(
            "Your machine does not support using the inference runner without a display."
        )

    if with_display:
        prepare_inference_runner_with_display(force_reset)
    else:
        prepare_inference_runner_without_display()


def launch_inference_runner(
    use_display: bool = typer.Option(
        ... if machine_supports_inference_without_display() else True,
        help="Run inference with or without a display",
        hidden=not machine_supports_inference_without_display(),
    ),
    dataset_split: TEAChDatasetSplit = typer.Option(
        ..., help="Choose with split to evaluate on", show_envvar=False
    ),
    clear_output_dir: bool = typer.Option(
        default=False,
        help="Clear the output directory to run on all the instances",
        show_envvar=False,
    ),
    limit_instances: Optional[int] = typer.Option(
        None,
        help="Optionally, randomly select a maximum number of instances to use during inference.",
        min=1,
    ),
) -> None:
    """Launch the inference runner for TEACh EDH instances."""
    if not use_display and not machine_supports_inference_without_display():
        raise typer.BadParameter(
            "Your machine does not support using the inference runner without a display."
        )

    with console.status("Preparing instances to evaluate on..."):
        if TEAChPaths.data_unused_edh_instances.exists():
            restore_unselected_edh_instances()

        if limit_instances:
            limit_edh_instances_evaluated(count=limit_instances, dataset_split=dataset_split)

    if use_display:
        launch_inference_runner_with_display(dataset_split, clear_output_dir)
    else:
        launch_inference_runner_without_display(dataset_split, clear_output_dir)


def stop_inference_runner_container() -> None:
    """Stop the Docker container running inference."""
    return stop_container(INFERENCE_RUNNER_CONTAINER_NAME)

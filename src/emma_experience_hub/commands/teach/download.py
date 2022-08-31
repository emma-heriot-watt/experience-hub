import logging
import random
import subprocess
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import Optional, cast

import boto3
import typer
from rich.console import Console
from rich.progress import BarColumn, MofNCompleteColumn, Progress, TextColumn, TimeRemainingColumn

from emma_experience_hub.commands.teach.constants import TEAChDatasetSplit, TEAChPaths


# Without this, boto print so many logs, it crashes the terminal.
logging.getLogger("boto3").setLevel(logging.CRITICAL)
logging.getLogger("botocore").setLevel(logging.CRITICAL)
logging.getLogger("nose").setLevel(logging.CRITICAL)
logging.getLogger("s3transfer").setLevel(logging.CRITICAL)
logging.getLogger("urllib3").setLevel(logging.CRITICAL)


console = Console()

progress = Progress(
    TextColumn("[bold blue]{task.description}", justify="right"),
    BarColumn(bar_width=None),
    "[progress.percentage]{task.percentage:>3.1f}%",
    MofNCompleteColumn(),
    TimeRemainingColumn(),
)


def download_models(
    remote_perception_checkpoint_uri: str = typer.Option(
        ...,
        envvar="REMOTE_PERCEPTION_CHECKPOINT_URI",
        help="URI for the Perception model file on S3.",
    ),
    remote_policy_checkpoint_uri: str = typer.Option(
        ..., envvar="REMOTE_POLICY_CHECKPOINT_URI", help="URI for the Policy model file on S3."
    ),
) -> None:
    """Download EMMA model files."""
    paths = TEAChPaths()

    paths.create_storage_dir()

    # Delete the previous model files if they exist
    if paths.policy_model.exists():
        paths.policy_model.unlink()
    if paths.perception_model.exists():
        paths.perception_model.unlink()

    # Download Models using S3
    subprocess.run(
        f"aws s3 cp {remote_perception_checkpoint_uri} {paths.policy_model.resolve()}",
        shell=True,
        check=True,
    )
    subprocess.run(
        f"aws s3 cp {remote_policy_checkpoint_uri} {paths.perception_model.resolve()}",
        shell=True,
        check=True,
    )


def download_games() -> None:
    """Download TEACh Games."""
    paths = TEAChPaths()

    for dataset_split in TEAChDatasetSplit:
        command = [
            "aws s3 cp",
            f"s3://emma-simbot/datasets/teach/games/{dataset_split.value}",
            str(paths.data.joinpath("games", dataset_split.value).resolve()),
            "--recursive",
        ]
        subprocess.run(" ".join(command), shell=True, check=True)


def download_edh_instances(
    dataset_split: TEAChDatasetSplit = typer.Option(..., help="Dataset split to download"),
    count: Optional[int] = typer.Option(
        None,
        help="Only download a number of EDH instances, chosen randomly.",
        min=1,
        show_envvar=False,
    ),
    download_images: bool = typer.Option(
        default=True, help="Download images for the EDH instances"
    ),
) -> None:
    """Download TEACh EDH instances."""
    paths = TEAChPaths()

    s3 = boto3.client("s3")

    with console.status("Getting all the paths to download..."):
        # Get URIs for all the EDH instances
        edh_instances_list: list[str] = [
            raw_object["Key"]
            for raw_object in s3.list_objects_v2(
                Bucket=paths.s3_bucket_name,
                Prefix=f"{paths.s3_edh_instances_prefix}/{dataset_split.value}",
            )["Contents"]
        ]

        # If desired, randomly sample from the list
        if count:
            edh_instances_list = random.sample(edh_instances_list, count)

    # Create progress bar tasks
    instances_task_id = progress.add_task("Downloading instances", total=len(edh_instances_list))

    with progress:
        # Create the output directory for the EDH instances
        instances_output_dir = paths.data.joinpath("edh_instances", dataset_split.value)
        instances_output_dir.mkdir(parents=True, exist_ok=True)

        # Download the EDH instances
        for instance_key in edh_instances_list:
            s3.download_file(
                Bucket=paths.s3_bucket_name,
                Key=instance_key,
                Filename=instances_output_dir.joinpath(instance_key.split("/")[-1]).as_posix(),
            )

            progress.advance(instances_task_id)

    if download_images:
        download_images_for_edh_instances(dataset_split)


def _get_available_images_for_edh_instance(
    edh_instance_id: str, *, dataset_split: TEAChDatasetSplit
) -> set[str]:
    """Return a set of image paths which should be downloaded for a given EDH instance.

    This also ensure that images which already exist are not downloaded.
    """
    s3 = boto3.client("s3")

    paths = TEAChPaths()
    images_dir = paths.data_images.joinpath(dataset_split.value)

    # If there are already some images downloaded, get a list of them
    existing_images = (
        {image.name for image in images_dir.joinpath(edh_instance_id).iterdir()}
        if images_dir.joinpath(edh_instance_id).exists()
        else set()
    )

    # Get a list of all the images that can be downloaded for the instance
    available_images_for_instance = (
        image_prefix["Key"]
        for image_prefix in s3.list_objects_v2(
            Bucket=paths.s3_bucket_name,
            Prefix="{images_prefix}/{split}/{instance}".format(
                images_prefix=paths.s3_images_prefix,
                split=dataset_split.value,
                instance=edh_instance_id.split(".")[0],
            ),
        )["Contents"]
        if "driver" in image_prefix["Key"]
    )

    # Filter out images which already exist
    image_prefixes_to_download: set[str] = {
        prefix
        for prefix in available_images_for_instance
        if prefix.split("/")[-1] not in existing_images
    }

    return image_prefixes_to_download


def download_images_for_edh_instances(
    dataset_split: TEAChDatasetSplit = typer.Option(..., help="Dataset split to download")
) -> None:
    """Download images for EDH instances."""
    s3 = boto3.client("s3")
    paths = TEAChPaths()

    with console.status("Getting list of downloaded instances..."):
        downloaded_edh_instance_ids = [
            instance.stem
            for instance in paths.data_edh_instances.joinpath(dataset_split.value).iterdir()
        ]

    task_id = progress.add_task("Determining which images to download...", start=False, total=0)

    with progress:
        with ThreadPoolExecutor() as pool:
            instance_image_prefixes_iterator = pool.map(
                partial(_get_available_images_for_edh_instance, dataset_split=dataset_split),
                downloaded_edh_instance_ids,
            )

            instance_image_prefixes_list = []

            for prefixes in instance_image_prefixes_iterator:
                instance_image_prefixes_list.append(prefixes)
                progress.update(
                    task_id, total=cast(float, progress.tasks[task_id].total) + len(prefixes)
                )

        for instance_image_keys in instance_image_prefixes_list:
            progress.update(task_id, description="Downloading images", start=True)

            for image_key in instance_image_keys:
                # Create the directory for all the images
                images_output_dir = paths.data.joinpath(
                    "images", dataset_split.value, image_key.split("/")[-2]
                )
                images_output_dir.mkdir(parents=True, exist_ok=True)

                # Download the images for the instance
                s3.download_file(
                    Bucket=paths.s3_bucket_name,
                    Key=image_key,
                    Filename=images_output_dir.joinpath(image_key.split("/")[-1]).as_posix(),
                )

                progress.advance(task_id)


def download_teach_data() -> None:
    """Download EVERYTHING related to TEACh.

    This just runs all the other commands sequentially.
    """
    download_games()
    download_edh_instances(TEAChDatasetSplit.valid_seen)
    download_edh_instances(TEAChDatasetSplit.valid_unseen)
    download_images_for_edh_instances(TEAChDatasetSplit.valid_seen)
    download_images_for_edh_instances(TEAChDatasetSplit.valid_unseen)

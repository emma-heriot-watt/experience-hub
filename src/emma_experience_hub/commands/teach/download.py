import itertools
import logging
import random
import subprocess
from typing import Optional

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

        # Get URIs all the necessary images for each EDH instances
        instance_image_prefixes_list: list[list[str]] = [
            [
                image_prefix["Key"]
                for image_prefix in s3.list_objects_v2(
                    Bucket=paths.s3_bucket_name,
                    Prefix="{images_prefix}/{split}/{instance}".format(
                        images_prefix=paths.s3_images_prefix,
                        split=dataset_split.value,
                        instance=edh_instance_prefix.split("/")[-1].split(".")[0],
                    ),
                )["Contents"]
                if "driver" in image_prefix["Key"]
            ]
            for edh_instance_prefix in edh_instances_list
        ]

    # Create a progress bar and the tasks
    progress = Progress(
        TextColumn("[bold blue]{task.description}", justify="right"),
        BarColumn(bar_width=None),
        "[progress.percentage]{task.percentage:>3.1f}%",
        "•",
        MofNCompleteColumn(),
        "•",
        TimeRemainingColumn(),
    )
    instances_task_id = progress.add_task("Downloading instances", total=len(edh_instances_list))

    images_task_id = progress.add_task(
        "Downloading images for instances",
        total=len(list(itertools.chain.from_iterable(instance_image_prefixes_list))),
    )

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

        for instance_image_keys in instance_image_prefixes_list:
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

                progress.advance(images_task_id)


def download_teach_data() -> None:
    """Download EVERYTHING related to TEACh.

    This just runs all the other commands sequentially.
    """
    download_games()
    download_edh_instances(TEAChDatasetSplit.valid_seen)
    download_edh_instances(TEAChDatasetSplit.valid_unseen)

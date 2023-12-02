import random
from typing import Optional

import typer
from rich.console import Console

from emma_datasets.datamodels.datasets.teach import TeachEdhInstance as TEAChEDHInstance
from emma_experience_hub.commands.teach.constants import TEAChDatasetSplit, TEAChPaths


console = Console()


def limit_edh_instances_evaluated(count: int, dataset_split: TEAChDatasetSplit) -> None:
    """Limit the number of instances being evalauted."""
    edh_instances_dir = TEAChPaths.data_edh_instances.joinpath(dataset_split.value)
    if count > len(list(edh_instances_dir.iterdir())):
        raise AssertionError(
            "The maximum number of instances is greater than the number of instances available."
        )

    temp_instances_dir = TEAChPaths.data_unused_edh_instances.joinpath(dataset_split.value)
    temp_instances_dir.mkdir(parents=True, exist_ok=True)

    all_instance_paths = list(edh_instances_dir.iterdir())
    selected_instances = random.sample(all_instance_paths, count)
    unselected_instances = (
        instance_path
        for instance_path in all_instance_paths
        if instance_path not in selected_instances
    )

    for instance_path in unselected_instances:
        instance_path.rename(temp_instances_dir.joinpath(instance_path.name))


def restore_unselected_edh_instances() -> None:
    """Restore EDH instances that were not evaluated on."""
    for instance_path in TEAChPaths.data_unused_edh_instances.rglob("*.json"):
        instance_path.rename(
            TEAChPaths.data_edh_instances.joinpath(
                instance_path.parent.parts[-1], instance_path.name
            )
        )

    for unused_dir in TEAChPaths.data_unused_edh_instances.iterdir():
        unused_dir.rmdir()
    TEAChPaths.data_unused_edh_instances.rmdir()


def filter_edh_instances(
    dataset_split: TEAChDatasetSplit = typer.Option(
        ..., help="Dataset split to perform filtering on"
    ),
    max_action_future_length: Optional[int] = typer.Option(
        None, help="Set the maximum length of the driver action futures for the instances."
    ),
    has_interaction_action_in_future: Optional[bool] = typer.Option(
        None, help="Ensure future actions contain at least one interaction action."
    ),
) -> None:
    """Filter EDH instances by a set of criteria."""
    paths = TEAChPaths()
    instances_dir = paths.data_edh_instances.joinpath(dataset_split.value)
    filtered_instances_dir = paths.data_filtered_edh_instances.joinpath(dataset_split.value)
    filtered_instances_dir.mkdir(parents=True, exist_ok=True)

    with console.status("Loading all EDH instances..."):
        edh_instances = [
            TEAChEDHInstance.parse_file(instance_path)
            for instance_path in instances_dir.iterdir()
            if instance_path.name.endswith("json")
        ]

    console.log(f"{len(edh_instances)} EDH instances found")

    if max_action_future_length:
        num_instances_before_filter = len(edh_instances)
        edh_instances = [
            instance
            for instance in edh_instances
            if len(instance.driver_actions_future) <= max_action_future_length
        ]
        console.log(
            f"{num_instances_before_filter - len(edh_instances)} EDH instances have more than {max_action_future_length} action in their future. {len(edh_instances)} EDH instances remaining..."
        )

    if has_interaction_action_in_future:
        num_instances_before_filter = len(edh_instances)
        edh_instances = [
            instance
            for instance in edh_instances
            if any(action.obj_interaction_action for action in instance.driver_actions_future)
        ]
        console.log(
            f"{num_instances_before_filter - len(edh_instances)} EDH instances [cyan]do not have an interaction action[/] in their future. {len(edh_instances)} EDH instances remaining..."
        )

    with console.status("Removing instances which do not match the filters..."):
        instance_names_to_keep = [f"{instance.instance_id}.json" for instance in edh_instances]

        for instance_path in instances_dir.iterdir():
            if instance_path.name in instance_names_to_keep:
                continue

            instance_path.rename(filtered_instances_dir.joinpath(instance_path.name))
            console.log(f"Removed {instance_path}")

    console.rule("Done!")
    console.log(
        "Run [u]`python -m emma_experience_hub teach restore-filtered-edh-instances`[/] to restore all the filtered instances."
    )


def restore_filtered_edh_instances() -> None:
    """Restore instances that have been previously filtered."""
    with console.status("Restoring instances which have been previously filtered..."):
        for instance_path in TEAChPaths.data_filtered_edh_instances.rglob("*.json"):
            instance_path.rename(
                TEAChPaths.data_edh_instances.joinpath(
                    instance_path.parent.parts[-1], instance_path.name
                )
            )

        for unused_dir in TEAChPaths.data_filtered_edh_instances.iterdir():
            unused_dir.rmdir()
        TEAChPaths.data_filtered_edh_instances.rmdir()

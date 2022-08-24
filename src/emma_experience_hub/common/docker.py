import subprocess

from rich.console import Console


console = Console()


def is_container_running(container_name: str) -> bool:
    """Check whether or not a container is currently running."""
    command = [
        "docker",
        "ps",
        f'--filter "name={container_name}"',
        "--filter status=running",
        '--format "{{.ID}}: {{.Command}}"',
    ]
    query = subprocess.run(" ".join(command), shell=True, check=True, stdout=subprocess.PIPE)
    return bool(query.stdout.decode("utf-8").strip())


def does_container_exist(container_name: str) -> bool:
    """Check whether or not a container exists."""
    command = [
        "docker",
        "ps",
        f'--filter "name={container_name}"',
        '--format "{{.ID}}: {{.Command}}"',
    ]
    query = subprocess.run(" ".join(command), shell=True, check=True, stdout=subprocess.PIPE)
    return bool(query.stdout.decode("utf-8").strip())


def stop_container(container_name: str) -> None:
    """Stop a running container, if it is running."""
    if is_container_running(container_name):
        with console.status("Container is running, shutting it down..."):
            subprocess.run(
                f"docker stop {container_name}", shell=True, check=True, stdout=subprocess.PIPE
            )
    else:
        console.log("Container not currently running.")
    if does_container_exist(container_name):
        with console.status("Container still exists, deleting..."):
            subprocess.run(
                f"docker rm {container_name}", shell=True, check=True, stdout=subprocess.PIPE
            )


def create_network_if_not_exists(network_name: str) -> None:
    """Create a network if one does not exist."""
    command = f"docker network inspect {network_name} >/dev/null 2>&1 || docker network create --driver bridge --internal {network_name}"

    subprocess.run(command, check=True, shell=True)

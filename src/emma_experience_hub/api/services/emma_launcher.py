import subprocess
from pathlib import Path


class EmmaServiceLauncher:
    """Run the various Emma services without dealing with the overhead."""

    def __init__(
        self,
        perception_repo_root: Path,
        policy_repo_root: Path,
        log_level: str = "debug",
    ) -> None:
        self._log_level = log_level

        self._perception_root = perception_repo_root
        self._policy_root = policy_repo_root

    def launch_perception(
        self,
        python_executable: Path,
        perception_config_path: Path,
        perception_model_checkpoint: Path,
    ) -> None:
        """Launch the perception API service."""
        run_command: list[str] = [
            str(python_executable),
            str(self._perception_root.joinpath("src/emma_perception/commands/run_server.py")),
            f'--config_file "{str(perception_config_path.resolve())}"',
            f'MODEL.WEIGHT "{str(perception_model_checkpoint.resolve())}"',
            'MODEL.ROI_HEADS.NMS_FILTER "1"',
            'MODEL.ROI_HEADS.SCORE_THRESH "0.2"',
            'TEST.IGNORE_BOX_REGRESSION "False"',
        ]

        subprocess.run(" ".join(run_command), shell=True, check=True)

    def launch_policy(self, python_executable: Path, policy_model_checkpoint: Path) -> None:
        """Launch the Policy API service."""
        run_command: list[str] = [
            str(python_executable),
            str(self._policy_root.joinpath("src/emma_perception/commands/run_server.py")),
        ]

        subprocess.run(" ".join(run_command), shell=True, check=True)


if __name__ == "__main__":
    launcher = EmmaServiceLauncher(
        Path.cwd().parent.joinpath("perception"),
        Path.cwd().parent.joinpath("policy"),
    )

    launcher.launch_perception(
        Path.cwd().parent.joinpath("perception/.venv/bin/python"),
        Path.cwd().parent.joinpath(
            "perception", "src/emma_perception/constants/vinvl_x152c4_alfred.yaml"
        ),
        Path.cwd().joinpath("storage/teach/models", "perception_model_checkpoint"),
    )

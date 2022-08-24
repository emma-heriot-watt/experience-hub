from enum import Enum
from pathlib import Path
from shutil import rmtree


DOCKER_NETWORK_NAME = "emma-teach-inference"
API_CONTAINER_NAME = "emma-teach-api"
FEATURE_EXTRACTOR_CONTAINER_NAME = "emma-teach-feature-extractor-api"
INFERENCE_RUNNER_CONTAINER_NAME = "teach-inference-runner"
INFERENCE_RUNNER_IMAGE_NAME = "heriot-watt/emma-simbot:teach-inference"
MODEL_DIR_WITHIN_CONTAINER = "/app/models"
FEATURE_EXTRACTOR_DEFAULT_PORT = "5500"
POLICY_API_DEFAULT_PORT = "5000"


class TEAChDatasetSplit(Enum):
    """Variants of dataset splits available for the TEACh dataset."""

    # all = "all"
    # train = "train"
    # valid = "valid"
    valid_seen = "valid_seen"
    valid_unseen = "valid_unseen"
    # test = "test"
    # test_seen = "test_seen"
    # test_unseen = "test_unseen"


class TEAChPaths:
    """Paths used for the TEACh API."""

    storage = Path.cwd().joinpath("storage/", "teach/")
    models = storage.joinpath("models/")

    output = storage.joinpath("output/")
    output_frames = output.joinpath("frames/")
    output_metadata = output.joinpath("metadata/")

    data = storage.joinpath("data/")
    data_images = data.joinpath("images/")
    data_edh_instances = data.joinpath("edh_instances/")
    data_games = data.joinpath("games/")
    data_unused_edh_instances = data.joinpath("_unused_edh_instances")

    policy_model = models.joinpath("policy_model_checkpoint")
    perception_model = models.joinpath("perception_model_checkpoint")

    alexa_teach_repo = storage.joinpath("alexa_teach_repo/")
    alexa_teach_repo_venv = alexa_teach_repo.joinpath(".venv/")
    alexa_teach_repo_python = alexa_teach_repo_venv.joinpath("bin/", "python")

    s3_bucket_name = "emma-simbot"
    s3_teach_prefix = "datasets/teach"
    s3_edh_instances_prefix = f"{s3_teach_prefix}/edh_instances"
    s3_images_prefix = f"{s3_teach_prefix}/images"

    def create_storage_dir(self) -> None:
        """Create the storage dir."""
        self.storage.mkdir(parents=True, exist_ok=True)

    def clear_output_dir(self) -> None:
        """Clear the output directory of all files."""
        rmtree(self.output)

    def create_output_dir(self, clear_output_dir: bool = False) -> None:
        """Create the output directories if they do not exist."""
        if clear_output_dir:
            self.clear_output_dir()

        output_dirs = [self.output_frames, self.output_metadata]

        for output_dir in output_dirs:
            output_dir.mkdir(parents=True, exist_ok=True)

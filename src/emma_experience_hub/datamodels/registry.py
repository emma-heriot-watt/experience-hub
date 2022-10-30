import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

from cloudpathlib import CloudPath
from convert_case import snake_case
from pydantic import BaseModel
from rich.progress import Progress


class ModelMetadata(BaseModel):
    """Metadata for the model."""

    s3_url: CloudPath
    version: str

    @property
    def file_safe_version(self) -> str:
        """Get the version without any unsafe characters."""
        return self.version.replace(".", "")

    def download_model(self, output_dir: Path) -> None:
        """Download the given model file."""
        self.s3_url.download_to(output_dir)


class ServiceMetadata(BaseModel):
    """Metadata for the services that we use."""

    _default_image_version: str = "latest"

    name: str
    image_repository_uri: str
    model: Optional[ModelMetadata] = None

    @property
    def image(self) -> str:
        """Get the URI for the docker image."""
        if self.model:
            return f"{self.image_repository_uri}:{self.model.version}"

        return f"{self.image_repository_uri}:{self._default_image_version}"

    @property
    def model_file_name(self) -> str:
        """Get the model file name for the service."""
        if self.model:
            return f"{self.name}-{self.model.file_safe_version}"

        return self.name

    def download_model(self, output_dir: Path, force: bool = False) -> None:
        """Download the model, if it's needed."""
        # Do nothing if there is no model
        if not self.model:
            return None

        # Do nothing if the model exists and we are not forcing download
        if self.model_exists(output_dir) and not force:
            return None

        # Download the model and rename it
        return self.model.download_model(output_dir.joinpath(self.model_file_name))

    def model_exists(self, output_dir: Path) -> bool:
        """Return True if the model already exists."""
        return output_dir.joinpath(self.model_file_name).exists()


class ServiceRegistry(BaseModel):
    """Registry of service metadata."""

    services: list[ServiceMetadata]

    image_env_var_suffix: str = "IMAGE"
    model_name_env_var_suffix: str = "MODEL"
    env_var_delimiter: str = "_"

    def __getitem__(self, index: int) -> ServiceMetadata:
        """Get metadata using the list index."""
        return self.services[index]

    def get_from_name(self, service_name: str) -> ServiceMetadata:
        """Get repository metadata from the repository name."""
        metadata_iterator = (
            metadata for metadata in self.services if metadata.name == service_name
        )
        return next(metadata_iterator)

    def download_all_models(self, output_dir: Path, force: bool = False) -> None:
        """Download all the models."""
        with Progress() as progress:
            task_id = progress.add_task("Downloading models...", total=len(self.services))

            with ThreadPoolExecutor() as executor:
                futures = {
                    executor.submit(service.download_model, output_dir, force)
                    for service in self.services
                }

                for _ in as_completed(futures):
                    progress.advance(task_id)

    def update_all_env_vars(self) -> None:
        """Update all the necessary environment variables to download and run the services."""
        for service in self.services:
            # Create the env variables
            service_name_prefix = snake_case(service.name).upper()
            image_env_var = (
                f"{service_name_prefix}{self.env_var_delimiter}{self.image_env_var_suffix}"
            )
            model_env_var = (
                f"{service_name_prefix}{self.env_var_delimiter}{self.model_name_env_var_suffix}"
            )

            # Set them
            os.environ[image_env_var] = service.image
            os.environ[model_env_var] = service.model_file_name

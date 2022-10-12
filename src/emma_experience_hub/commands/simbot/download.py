from pydantic import BaseModel, FilePath, HttpUrl


class ModelMetadata(BaseModel):
    """Metadata information for a model file."""

    s3_path: str
    local_path: FilePath
    repository_url: HttpUrl
    repository_version: str


def download_models() -> None:
    """Download models into the model directory, so it can be used by the services.

    Also create a JSON file which tracks their original name, the repository supported version, and
    more.
    """

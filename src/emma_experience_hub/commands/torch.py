import logging
import subprocess
from decimal import Decimal
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler


console = Console()

logging.basicConfig(
    level="NOTSET",
    format="%(message)s",  # noqa: WPS323
    datefmt="[%X]",  # noqa: WPS323
    handlers=[RichHandler(console=console, markup=True, rich_tracebacks=True)],
)
log = logging.getLogger("rich")


def is_cuda_available() -> bool:
    """Check if CUDA is available, without global torch import."""
    import torch  # noqa: WPS433

    return torch.cuda.is_available()


def get_torch_version() -> tuple[str, Optional[str]]:
    """Get the current version of PyTorch, without global torch import.

    If it is for a specific version, it will have the '+cu11x' suffix.
    """
    import torch  # noqa: WPS433

    version = torch.__version__

    log.info(f"Current `torch` verison: {version}")

    if "+" not in version:
        return version, None

    return version.split("+")[0], version.split("+")[1]


def get_supported_cuda_version() -> Decimal:
    """Get the highest supported CUDA version.

    NVIDIA-SMI seems to be the most consistent version display, so needed to use subprocess to get
    it out.
    """
    nvidia_smi_process = subprocess.Popen(
        ["nvidia-smi"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    nvidia_smi_stdout, _ = nvidia_smi_process.communicate()

    cuda_version_line = nvidia_smi_stdout.decode().split("\n")[2]
    cuda_version_list = list(filter(None, cuda_version_line.split(" ")))
    cuda_version = float(cuda_version_list[-2])

    log.info(f"Supported CUDA version: {cuda_version}")

    return Decimal(cuda_version)


def get_torch_cuda_suffix(cuda_version: Decimal) -> str:
    """Get the relevant CUDA suffix from the version."""
    is_greater_than11 = cuda_version.compare(11) > 0  # noqa: WPS432
    is_greater_than113 = cuda_version.compare(Decimal(11.3)) > 0  # noqa: WPS432
    is_greater_than116 = cuda_version.compare(Decimal(11.6)) > 0  # noqa: WPS432

    if is_greater_than11 and not is_greater_than113:
        return "cu111"

    if is_greater_than113 and not is_greater_than116:
        return "cu113"

    if is_greater_than116:
        return "cu116"

    return ""

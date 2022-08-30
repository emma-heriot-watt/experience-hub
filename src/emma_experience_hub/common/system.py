import os
import platform
from functools import cache

from emma_experience_hub.common.torch import is_cuda_available


@cache
def machine_supports_inference_without_display() -> bool:
    """Validate that the current machine is able to launch the inference runner with Docker.

    Conditions:
        1. CUDA must be available
        2. This application must be running Linux
    """
    conditions: list[bool] = [
        is_cuda_available(),
        platform.system().lower() == "linux",
    ]

    # All conditions must be true for Docker to be allowed
    return all(conditions)


def get_active_display_index() -> int:
    """Get the index of the currently active display, if available."""
    if not machine_supports_inference_without_display():
        raise AssertionError("Machine does not support running an XServer display")

    display_index = os.environ.get("DISPLAY")

    if not display_index:
        raise AssertionError("Environment variable `$DISPLAY` is not set")

    return int(display_index)


def is_xserver_display_running() -> bool:
    """Check whether or not the X Server display is running."""
    try:
        get_active_display_index()
    except AssertionError:
        return False

    return True

import os
import platform
import re
import shlex
import subprocess
import tempfile
from typing import Any

from rich.console import Console


console = Console()


def pci_records() -> list[dict[str, Any]]:
    """Get the PCI records?"""
    records = []
    command = shlex.split("lspci -vmm")
    output = subprocess.check_output(command).decode()

    for devices in output.strip().split("\n\n"):
        record: dict[str, Any] = {}
        records.append(record)
        for row in devices.split("\n"):
            key, device_row_value = row.split("\t")
            record[key.split(":")[0]] = device_row_value

    return records


def generate_xorg_conf(devices: list[Any]) -> str:
    """Generate a config for Xorg."""
    xorg_conf = []

    device_section = """
Section "Device"
    Identifier     "Device{device_id}"
    Driver         "nvidia"
    VendorName     "NVIDIA Corporation"
    BusID          "{bus_id}"
EndSection
"""
    server_layout_section = """
Section "ServerLayout"
    Identifier     "Layout0"
    {screen_records}
EndSection
"""
    screen_section = """
Section "Screen"
    Identifier     "Screen{screen_id}"
    Device         "Device{device_id}"
    DefaultDepth    24
    Option         "AllowEmptyInitialConfiguration" "True"
    SubSection     "Display"
        Depth       24
        Virtual 1250 1250
    EndSubSection
EndSection
"""
    screen_records = []
    for i, bus_id in enumerate(devices):
        xorg_conf.append(device_section.format(device_id=i, bus_id=bus_id))
        xorg_conf.append(screen_section.format(device_id=i, screen_id=i))
        screen_records.append('Screen {screen_id} "Screen{screen_id}" 0 0'.format(screen_id=i))

    xorg_conf.append(server_layout_section.format(screen_records="\n    ".join(screen_records)))

    output = "\n".join(xorg_conf)
    console.print(output)
    return output


def startx(display: int) -> None:  # noqa: WPS231
    """Start the X server."""
    if platform.system() != "Linux":
        raise OSError("Can only run startx on linux")

    devices = []

    for record in pci_records():
        is_valid_vendor = record.get("Vendor", "") == "NVIDIA Corporation"
        is_valid_record_class = record["Class"] in {"VGA compatible controller", "3D controller"}

        if is_valid_vendor and is_valid_record_class:
            bus_id_list = [
                str(int(slot, 16)) for slot in re.split(r"[:\.]", record["Slot"])  # noqa: WPS432
            ]
            bus_id = f"PCI:{':'.join(bus_id_list)}"
            devices.append(bus_id)

    if not devices:
        raise RuntimeError("No NVIDIA cards found")

    fd, path = tempfile.mkstemp()
    with open(path, "w") as f:
        f.write(generate_xorg_conf(devices))

    command = shlex.split(
        f"Xorg -noreset +extension GLX +extension RANDR +extension RENDER -config {path} :{display}"
    )

    # Create an environment variable for the display
    if not os.environ["DISPLAY"]:
        os.environ["DISPLAY"] = str(display)

    try:  # noqa: WPS501
        subprocess.call(command)
    finally:
        os.close(fd)
        os.unlink(path)

        # Remove the display environment variable if it exists
        if os.environ["DISPLAY"]:
            del os.environ["DISPLAY"]  # noqa: WPS420


def launch_xserver() -> None:
    """Launch the X Server (needed if running inference without a display).

    This just runs a mildly modified version of the one from alexa/teach.
    """
    display = 0
    # if len(sys.argv) > 1:
    #     display = int(sys.argv[1])
    console.print(f"Starting X on DISPLAY=:{display}")
    startx(display)

import torch

from emma_experience_hub.datamodels.simbot.payloads import SimBotObjectMaskType


class CompressSegmentationMask:
    """Refactored version of their compress mask function.

    Just to make a bit more sense of it.
    """

    __slots__ = ("run_idx", "run_length", "compressed_mask", "current_run")

    def __init__(self) -> None:
        self.run_idx = 0
        self.run_length = 0
        self.compressed_mask: SimBotObjectMaskType = []
        self.current_run = False

    def __call__(self, mask: torch.Tensor) -> SimBotObjectMaskType:
        """Compress the mask."""
        self.reset()

        for x_idx in range(mask.size(0)):
            for y_idx in range(mask.size(1)):
                self.step(mask, x_idx, y_idx)

        return self.compressed_mask

    def reset(self) -> None:
        """Reset the state of the class."""
        self.run_idx = 0
        self.run_length = 0
        self.compressed_mask = []
        self.current_run = False

    def step(self, mask: torch.Tensor, x_idx: int, y_idx: int) -> None:
        """Take step in loop."""
        if mask[x_idx][y_idx] == 1 and not self.current_run:
            self.start_new_run()

        if mask[x_idx][y_idx] == 0 and self.current_run:
            self.end_current_run()

        if self.current_run:
            self.run_length += 1

        self.run_idx += 1

    def start_new_run(self) -> None:
        """Start a new run to compress."""
        self.current_run = True
        self.compressed_mask.append([self.run_idx, 0])

    def end_current_run(self) -> None:
        """End the current run."""
        self.current_run = False
        self.compressed_mask[-1][1] = self.run_length
        self.run_length = 0


def compress_segmentation_mask(mask: torch.Tensor) -> SimBotObjectMaskType:
    """Compress the segmenmtation mask for the arena."""
    return CompressSegmentationMask()(mask)

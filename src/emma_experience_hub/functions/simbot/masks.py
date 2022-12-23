import torch

from emma_experience_hub.datamodels.simbot.payloads import SimBotObjectMaskType


def compress_segmentation_mask(mask: torch.Tensor) -> SimBotObjectMaskType:  # noqa: WPS231
    """Compress the segmenmtation mask for the arena."""
    run_len_compressed: SimBotObjectMaskType = []
    idx = 0
    curr_run = False
    run_len = 0

    for x_idx, _ in enumerate(mask):
        for y_idx, _ in enumerate(mask[x_idx]):
            if mask[x_idx][y_idx] == 1 and not curr_run:
                curr_run = True
                run_len_compressed.append([idx, 0])
            if mask[x_idx][y_idx] == 0 and curr_run:
                curr_run = False
                run_len_compressed[-1][1] = run_len
                run_len = 0
            if curr_run:
                run_len += 1
            idx += 1
    if curr_run:
        run_len_compressed[-1][1] = run_len

    return run_len_compressed

import torch
from hypothesis import given, strategies as st
from pytest_benchmark.fixture import BenchmarkFixture
from pytest_cases import fixture

from emma_experience_hub.functions.simbot.masks import (
    alexa_compress_segmentation_mask,
    tensor_compress_segmntation_mask,
)


@fixture(scope="module")
def mask() -> torch.Tensor:
    """Maxk for the benchmark."""
    mask_size = 300
    return torch.randint(0, 2, (mask_size, mask_size))


@st.composite
def create_random_mask(
    draw: st.DrawFn, mask_size: st.SearchStrategy[int] = st.integers(1, 20)
) -> torch.Tensor:
    drawn_mask_size = draw(mask_size)
    return torch.randint(0, 2, (drawn_mask_size, drawn_mask_size))


def test_alexa_compress_mask_benchmark(mask: torch.Tensor, benchmark: BenchmarkFixture) -> None:
    compressed_mask = benchmark(alexa_compress_segmentation_mask, mask)
    assert compressed_mask


def test_tensor_compress_mask_benchmark(mask: torch.Tensor, benchmark: BenchmarkFixture) -> None:
    compressed_mask = benchmark(tensor_compress_segmntation_mask, mask)
    assert compressed_mask


@given(mask=create_random_mask())
def test_tensor_compress_mask_equals_alexa(mask: torch.Tensor) -> None:
    alexa_compressed_mask = alexa_compress_segmentation_mask(mask)
    tensor_compressed_mask = tensor_compress_segmntation_mask(mask)
    assert alexa_compressed_mask == tensor_compressed_mask

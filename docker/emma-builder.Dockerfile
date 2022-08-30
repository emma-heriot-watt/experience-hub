ARG IMAGE_BASE_NAME

FROM ${IMAGE_BASE_NAME}:base-poetry

ARG REMOTE_REPO_URL
ARG REMOTE_REPO_BRANCH
ARG TORCH_VERSION_SUFFIX

# Only get the dependency files
WORKDIR ${PYSETUP_PATH}/repo
RUN git clone -b "${REMOTE_REPO_BRANCH}" --single-branch "${REMOTE_REPO_URL}" . \
	&& cp pyproject.toml poetry.lock "${PYSETUP_PATH}"

WORKDIR $PYSETUP_PATH
RUN poetry install --no-dev --no-root

# Install the correct torch version for CUDA
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN TORCH_VERSION="$(pip show torch | grep Version | cut -d ':' -f2 | xargs)${TORCH_VERSION_SUFFIX}" \
	&& TORCHVISION_VERSION="$(pip show torchvision | grep Version | cut -d ':' -f2 | xargs)${TORCH_VERSION_SUFFIX}" \
	&& pip install --no-cache-dir torch=="${TORCH_VERSION}" torchvision=="${TORCHVISION_VERSION}" -f https://download.pytorch.org/whl/torch_stable.html

# Install scene graph benchmark
# hadolint ignore=DL3013
RUN pip install poethepoet --no-cache-dir \
	&& poetry run poe install-everything-else

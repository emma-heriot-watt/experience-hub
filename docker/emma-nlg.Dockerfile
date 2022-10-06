ARG IMAGE_BASE_NAME

FROM ${IMAGE_BASE_NAME}:base-poetry

ARG REMOTE_REPO_URL
ARG REMOTE_REPO_BRANCH

# Only get the dependency files
WORKDIR ${PYSETUP_PATH}/repo
RUN git clone -b "${REMOTE_REPO_BRANCH}" --single-branch --depth=1 "${REMOTE_REPO_URL}" . && \
	poetry install

# Set the PYTHONPATH
ENV PYTHONPATH='./src'

ENTRYPOINT ["/bin/bash"]

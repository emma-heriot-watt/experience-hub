ARG IMAGE_BASE_NAME

# Load the images as previous stages
FROM ${IMAGE_BASE_NAME}:perception as builder__perception
FROM ${IMAGE_BASE_NAME}:policy as builder__policy

# Load the base image
ARG IMAGE_BASE_NAME
FROM ${IMAGE_BASE_NAME}:base

WORKDIR /app

# Copy the venvs and repos
COPY --from=builder__perception ${VIRTUAL_ENV} ./perception/.venv
COPY --from=builder__perception ${PYSETUP_PATH}/repo ./perception/

COPY --from=builder__policy ${VIRTUAL_ENV} ./policy/.venv
COPY --from=builder__policy ${PYSETUP_PATH}/repo ./policy/

# Install packages as editable
RUN cd ./perception \
	&& . .venv/bin/activate \
	&& pip install --no-deps -e .

RUN cd ./policy \
	&& . .venv/bin/activate \
	&& pip install --no-deps -e .

# Set the PYTHONPATH
ENV PYTHONPATH='./src'

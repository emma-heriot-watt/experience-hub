ARG IMAGE_BASE_NAME

FROM ${IMAGE_BASE_NAME}:base

WORKDIR $PYSETUP_PATH

RUN curl -sSL https://install.python-poetry.org | python3 - \
	&& python -m venv $VIRTUAL_ENV \
	&& pip install -U pip --no-cache-dir \
	# Setuptools v59.5.0 used because torch/lightining version used requires it
	&& pip install setuptools==59.5.0 --no-cache-dir

# Add Poetry to the path
ENV PATH="$POETRY_HOME/bin:${PATH}"

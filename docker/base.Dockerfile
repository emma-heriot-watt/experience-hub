
ARG PYTHON_VERSION

FROM python:${PYTHON_VERSION}-slim-bullseye

ENV PYTHONUNBUFFERED=1 \
	PYTHONDONTWRITEBYTECODE=1 \
	# Pip
	PIP_NO_CACHE_DIR=off \
	PIP_DISABLE_PIP_VERSION_CHECK=on \
	PIP_DEFAULT_TIMEOUT=100 \
	# Poetry
	POETRY_HOME="/opt/poetry" \
	POETRY_VIRTUALENVS_CREATE=false \
	POETRY_VIRTUALENVS_IN_PROJECT=false \
	POETRY_CACHE_DIR="/opt/poetry/cache" \
	POETRY_NO_INTERACTION=1 \
	# Venv
	PYSETUP_PATH="/opt/pysetup" \
	VIRTUAL_ENV="/opt/pysetup/.venv"

ENV PATH="$VIRTUAL_ENV/bin:$POETRY_HOME/bin:$PATH"

RUN apt-get update -qq \
	&& apt-get upgrade -y --no-install-recommends \
	build-essential \
	curl \
	git \
	ffmpeg libsm6 libxext6 \
	&& apt-get clean \
	&& rm -rf /var/lib/apt/lists/* \
	&& apt-get autoremove -y

# Allow access to EMMA simbot repos, without exposing secrets
WORKDIR /
COPY docker/helpers/add-pat-to-git.sh .
RUN --mount=type=secret,id=GITHUB_PAT bash ./add-pat-to-git.sh

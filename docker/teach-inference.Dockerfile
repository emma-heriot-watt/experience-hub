FROM ubuntu:18.04

# install python3.8
# hadolint ignore=DL3008
RUN apt-get update -qq \
	&& apt-get install --no-install-recommends -y build-essential software-properties-common \
	&& add-apt-repository -y ppa:deadsnakes/ppa \
	&& apt-get install --no-install-recommends -y python3.8 python3.8-dev python3.8-distutils \
	&& apt-get clean \
	&& rm -rf /var/lib/apt/lists/* \
	&& apt-get autoremove -y

# register the version in alternatives and set higher priority to 3.8
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.6 1
# hadolint ignore=DL3059
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.8 2

# hadolint ignore=DL3027
RUN apt update && DEBIAN_FRONTEND=noninteractive apt install -y --no-install-recommends \
	ffmpeg \
	vim \
	curl \
	git

# upgrade pip to latest version
RUN curl -s https://bootstrap.pypa.io/get-pip.py -o get-pip.py && \
	python3 get-pip.py --force-reinstall && \
	rm get-pip.py

# Create a folder for the app
WORKDIR /app

RUN git clone https://github.com/alexa/teach.git .
# hadolint ignore=DL3059
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH ./src

RUN pip install --no-cache-dir -e .

# Download AI2Thor executable
# hadolint ignore=DL3059
RUN python3 -c "from teach.settings import get_settings; from teach.simulators.simulator_THOR import COMMIT_ID, TEAChController; TEAChController(base_dir=get_settings().AI2THOR_BASE_DIR, download_only=True, commit_id=COMMIT_ID);"

CMD ["/bin/bash"]

# EMMA SimBot: Experience Hub

## Installing the repo

Like other repos in EMMA, we advocate for pyenv and Poetry for managing the project. To get setup with this repository, just run the following:

```bash
pyenv install 3.9.13
pyenv local 3.9.13
poetry env use $(pyenv which python)
poetry install
poetry shell
```

## Building Docker images

We've tried to make it as easy as possible to build the Docker images for EMMA, containing all the necessary components you will need to run EMMA.

### Prerequisites

1. We assume you have already installed the project and have activated the virtual environment (using `poetry shell`)
1. You need the latest version of Docker
1. Make sure Docker is running

### Building the images

Run ` python -m emma_experience_hub docker build` and wait for it to build all the images.

#### What about torch CUDA versions?

We extract the current CUDA version from `nvidia-smi` and use the CUDA variant available.

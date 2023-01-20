# EMMA SimBot: Experience Hub

## Installing the repo

Like other repos in EMMA, we advocate for pyenv and Poetry for managing the project. To get setup with this repository, just run the following:

```bash
pyenv install
poetry env use $(pyenv which python)
poetry install
poetry shell
```

## How to do things with the CLI

There are more commands than mentioned here. For more details regarding _any command_, just add `--help`!

## How to update the service registry for SimBot

To change the models that are being used, update the file within `storage/registry/simbot/`

For example, to change the models being used in production, update `storage/registry/models/production.yml`. This change will propagate to all future actions.

## What if I need `sudo` with Docker?

If you need `sudo` to run Docker, you need to also use the `-E` flag — i.e., use `sudo -E` to run the commands.

If it can't find the python path to the venv used for this installation, you can get the executable path from `which python` and then export it into a new variable.

Assuming you've already installed and activated the virtualenv as above, you can run the following:

```bash
export LOCAL_PYTHON=$(which python)
sudo -E $LOCAL_PYTHON -m emma_experience_hub
```

## Running the staging environment

Assuming you have an EC2 instance already created, connect to the instance, and use tmux to create two panels. In the first panel, we need to
run all the background services required for EMMA (e.g., policy, NLU, etc.). To do so we use Docker
compose and it can be run as follows (for this you must use `sudo`):

```
sudo -E <PATH_TO_PYTHON_EXECUTABLE> -m emma_experience_hub simbot run-background-services

```

Then, in the second tab you can run the experience hub:

```
python -m emma_experience_hub simbot run-controller-api --auxiliary-metadata-dir ../staging_auxiliary_metadata --auxiliary-metadata-cache-
dir ../cache/auxiliary_metadata --extracted-features-cache-dir ../cache/features
```

Make sure that all the services are up and running. Happy debugging!

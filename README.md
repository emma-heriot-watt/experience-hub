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

## How to do things with the CLI

There are more commands than mentioned here. To see what you can do with any command, just add `--help`.

### Prerequisites

1. You have already installed the project and have activated the virtual environment (as above using `poetry shell`)
1. You have the latest version of Docker and it is running
1. Create a `.env` file, and use the `.env.example` to add variables

### Building the Docker images for EMMA

We've tried to make it as easy as possible to build the Docker images for EMMA, containing all the necessary components you will need to run EMMA. Run ` python -m emma_experience_hub build-emma` and wait for it to build all the images.

#### What about torch CUDA versions?

We extract the current CUDA version from `nvidia-smi` and use the CUDA variant available. It should be automatic. If not, check out the `--help` on the command to see how to include it yourself.

### Running the inference runner with TEACh EDH instances

Running TEACh with EMMA is now easy!! Note that you can still add `--help` to any command to see all the options.

#### Preparing to run the inference

1. Build EMMA with `python -m emma_experience_hub build-emma`
2. Download and prepare TEACh with `python -m emma_experience_hub teach prepare-everything`
3. In a tmux pane, run the API and specify the dataset split you're using (with `python -m emma_experience_hub teach launch-api --dataset-split [valid_seen|valid_unseen]`)

#### Running inference _with a display_

These set of commands will ensure that everything is setup to run the inference on your own machine.

4. In another tmux pane, run the inference runner with `python -m emma_experience_hub teach launch-inference-runner --with-display --dataset-split [valid_seen|valid_unseen]`

#### Running inference _without a display_

4. With tmux or similar, run the X server (with `python -m emma_experience_hub teach launch-xserver`)
5. Run the inference runner and specify the dataset split you're using with `python -m emma_experience_hub teach launch-inference-runner --without-display --dataset-split [valid_seen|valid_unseen]`

#### Watching metrics compute

To see the results of the inference runner **and watch them update**, run `python -m emma_experience_hub teach compute-metrics --watch`.

#### How to only download a given number of EDH instances?

To only download a limited number of instances, run `python -m emma_experience_hub teach download-edh-instances` with the `--count <NUMBER>`

#### How to only perform inference on a given number of instances?

To perform inference on a set maximum of instances, run `python -m emma_experience_hub teach launch-inference-runner` with the flag `--limit-instances [INTEGER]`.

### What if I need `sudo` with Docker?

If you need `sudo` to run Docker, you need to also use the `-E` flag — i.e., use `sudo -E` to run the commands.

If it can't find the python path to the venv used for this installation, you can get the executable path from `which python` and then export it into a new variable.

Assuming you've already installed and activated the virtualenv as above, you can run the following:

```bash
export LOCAL_PYTHON=$(which python)
sudo -E $LOCAL_PYTHON -m emma_experience_hub
```

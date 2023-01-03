#!/usr/bin/env bash

GITHUB_PAT=$1

# ---------------------------- Install GitHub CLI ---------------------------- #
type -p curl >/dev/null || sudo apt install curl -y
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg &&
	sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg &&
	echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list >/dev/null &&
	sudo apt update &&
	sudo apt install gh -y

gh auth login --with-token "${GITHUB_PAT}"

# ---------------------- Install pyenv for python sanity --------------------- #
curl https://pyenv.run | bash

# --------------------- Update the shell config for bash --------------------- #
# shellcheck disable=SC2016
{
	echo 'export PYENV_ROOT="$HOME/.pyenv"'
	echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"'
	echo 'eval "$(pyenv init -)"'
	echo 'eval "$(pyenv virtualenv-init -)"'
} >>~/.bashrc

# ------------------------------ Install Poetry ------------------------------ #
curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to the PATH
echo "export PATH='/home/ubuntu/.local/bin:$PATH'" >>~/.bashrc

# Create venvs within the project
poetry config virtualenvs.in-project true

# Handle temporary poetry issue
# https://github.com/python-poetry/poetry/issues/1917#issuecomment-1251667047
echo 'export PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring' >>~/.bashrc

# Add poethepoet for all the poetry hooks
poetry self add 'poethepoet[poetry_plugin]'

# --------------------- Install Python build dependencies -------------------- #
sudo apt update -y &&
	sudo apt install -y make build-essential libssl-dev zlib1g-dev \
		libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
		libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev

# ------------------------------ Set tmux color ------------------------------ #
echo 'set -g default-terminal "screen-256color"' >>~/.tmux.conf

# ------------------------------- Install CUDA ------------------------------- #
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-ubuntu2004.pin &&
	sudo mv cuda-ubuntu2004.pin /etc/apt/preferences.d/cuda-repository-pin-600 &&
	sudo apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/3bf863cc.pub &&
	sudo add-apt-repository "deb https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/ /" &&
	sudo apt update -y &&
	sudo apt install -y cuda

# ------------------------------ Install Docker ------------------------------ #
curl -fsSL https://download.docker.com/linux/ubuntu/gpg |
	sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg &&
	echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" |
	sudo tee /etc/apt/sources.list.d/docker.list >/dev/null &&
	sudo apt update -y &&
	sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# -------------------------- Install nvidia-docker2 -------------------------- #
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
# shellcheck source=/dev/null
distribution=$(
	. /etc/os-release
	echo "$ID""$VERSION_ID"
) && {
	curl -s -L https://nvidia.github.io/libnvidia-container/"$distribution"/libnvidia-container.list |
		sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' |
		sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
}
sudo apt update -y &&
	sudo apt install -y nvidia-docker2 &&
	sudo systemctl restart docker

# ------------------------------ Install AWS CLI ----------------------------- #
sudo apt install -y unzip
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# ------------------------------- Login to AWS ------------------------------- #
aws configure --profile TeamProfile
# TODO: Configure profile

# ---------------------------- Enable AWS Profile ---------------------------- #ç
export AUS_PROFILE=TeamProfile

# ---------------------------- Install NFS common ---------------------------- #
sudo apt-get -y install nfs-common

# ------------------------- Install Amazon EFS Utils ------------------------- #
sudo apt-get -y install git binutils
git clone https://github.com/aws/efs-utils .aws-utils
cd .aws-utils || exit
./build-deb.sh
sudo apt-get -y install ./build/amazon-efs-utils*deb

# ---------------------------- Create dir for EMMA --------------------------- #
mkdir emma
cd emma || exit

# ----------------------- Connect EFS for SimBot cache ----------------------- #
mkdir cache
sudo mount -t efs -o tls,accesspoint=fsap-09425fce1a442352e fs-09152325b5864bf9f:/ cache
sudo chmod 777 cache
echo "fs-09152325b5864bf9f:/ /home/ubuntu/emma/cache efs _netdev,noresvport,tls,iam,accesspoint=fsap-09425fce1a442352e 0 0" | sudo tee -a /etc/fstab

# -------------------- Connect EFS for auxiliary metadata -------------------- #
mkdir auxiliary_metadata
echo 10.0.112.83 fs-0bfa9bdb8b799cb84.efs.us-east-1.amazonaws.com | sudo tee -a /etc/hosts
sudo mount -t efs -o tls,accesspoint=fsap-022169cf9e6e76aa9 fs-0bfa9bdb8b799cb84 auxiliary_metadata
echo "fs-0bfa9bdb8b799cb84:/ /home/ubuntu/emma/auxiliary_metadata efs _netdev,noresvport,tls,iam,accesspoint=fsap-022169cf9e6e76aa9 0 0" | sudo tee -a /etc/fstab

# ----------------- Setup EFS for staging auxiliary metadata ----------------- #
mkdir staging_auxiliary_metadata
echo 10.0.96.154 fs-02d492af78a2f5b1a.efs.us-east-1.amazonaws.com | sudo tee -a /etc/hosts
sudo mount -t efs -o tls,accesspoint=fsap-01eda13760c255e37 fs-02d492af78a2f5b1a staging_auxiliary_metadata
echo "fs-02d492af78a2f5b1a:/ /home/ubuntu/emma/staging_auxiliary_metadata efs _netdev,noresvport,tls,iam,accesspoint=fsap-01eda13760c255e37 0 0" | sudo tee -a /etc/fstab

# ----------------------- Import experience-hub project ---------------------- #
git clone https://github.com/emma-simbot/experience-hub experience-hub &&
	cd experience-hub || exit

# -------------------------- Prepare Experience hub -------------------------- #
pyenv install
poetry env use "$(pyenv which python)"

# ----------------------------- Authenticate ECR ----------------------------- #
aws ecr get-login-password --region us-east-1 | sudo docker login --username AWS --password-stdin 020417957102.dkr.ecr.us-east-1.amazonaws.com

# ------------------------------- Restart shell ------------------------------ #
exec "$SHELL"

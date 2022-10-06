variable "IMAGE_NAME" {
  default = "heriot-watt/emma-simbot"
}

variable "PYTHON_VERSION" {
  default = "3.9"
}

variable "TORCH_VERSION_SUFFIX" {
  default = ""
}

variable "PERCEPTION_REPO_BRANCH" {
  default = "main"
}

variable "POLICY_REPO_BRANCH" {
  default = "main"
}

group "base-images" {
  targets = ["base", "base-poetry"]
}

target "base" {
  dockerfile = "docker/base.Dockerfile"
  tags       = ["${IMAGE_NAME}:base"]

  args = {
    PYTHON_VERSION = "${PYTHON_VERSION}"
  }

  secret = ["id=GITHUB_PAT"]
}

target "base-poetry" {
  dockerfile = "docker/base-poetry.Dockerfile"
  tags       = ["${IMAGE_NAME}:base-poetry"]

  args = {
    IMAGE_BASE_NAME = "${IMAGE_NAME}"
  }
}

target "profanity-filter" {
  dockerfile = "docker/profanity-filter.Dockerfile"
  tags       = ["${IMAGE_NAME}:profanity-filter"]

  args = {
    IMAGE_BASE_NAME    = "${IMAGE_NAME}"
    REMOTE_REPO_URL    = "https://github.com/emma-simbot/profanity-filter"
    REMOTE_REPO_BRANCH = "master"
  }
}

target "nlg" {
  dockerfile = "docker/emma-nlg.Dockerfile"
  tags       = ["${IMAGE_NAME}:nlg"]

  args = {
    IMAGE_BASE_NAME    = "${IMAGE_NAME}"
    REMOTE_REPO_URL    = "https://github.com/emma-simbot/nlg"
    REMOTE_REPO_BRANCH = "main"
  }
}

group "emma-modules" {
  targets = ["emma-perception", "emma-policy"]
}

target "emma-perception" {
  dockerfile = "docker/emma-builder.Dockerfile"
  tags       = ["${IMAGE_NAME}:perception"]

  args = {
    REMOTE_REPO_URL      = "https://github.com/emma-simbot/perception"
    REMOTE_REPO_BRANCH   = "${PERCEPTION_REPO_BRANCH}"
    IMAGE_BASE_NAME      = "${IMAGE_NAME}"
    TORCH_VERSION_SUFFIX = "${TORCH_VERSION_SUFFIX}"
  }
}

target "emma-policy" {
  dockerfile = "docker/emma-builder.Dockerfile"
  tags       = ["${IMAGE_NAME}:policy"]

  args = {
    REMOTE_REPO_URL      = "https://github.com/emma-simbot/policy"
    REMOTE_REPO_BRANCH   = "${POLICY_REPO_BRANCH}"
    IMAGE_BASE_NAME      = "${IMAGE_NAME}"
    TORCH_VERSION_SUFFIX = "${TORCH_VERSION_SUFFIX}"
  }
}

target "emma-full" {
  dockerfile = "docker/emma-full.Dockerfile"
  tags       = ["${IMAGE_NAME}:full"]

  args = {
    IMAGE_BASE_NAME = "${IMAGE_NAME}"
  }
}

target "teach-inference" {
  dockerfile = "docker/teach-inference.Dockerfile"
  tags       = ["${IMAGE_NAME}:teach-inference"]
}

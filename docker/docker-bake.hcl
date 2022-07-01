variable "IMAGE_NAME" {
  default = "heriot-watt/emma-simbot"
}

variable "PYTHON_VERSION" {
  default = "3.9"
}

variable "TORCH_VERISON_SUFFIX" {
  default = ""
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


group "emma-modules" {
  targets = ["emma-perception", "emma-policy"]
}

target "emma-perception" {
  dockerfile = "docker/emma-builder.Dockerfile"
  tags       = ["${IMAGE_NAME}:perception"]

  args = {
    REMOTE_REPO_URL      = "https://github.com/emma-simbot/perception"
    IMAGE_BASE_NAME      = "${IMAGE_NAME}"
    TORCH_VERISON_SUFFIX = "${TORCH_VERISON_SUFFIX}"
  }
}

target "emma-policy" {
  dockerfile = "docker/emma-builder.Dockerfile"
  tags       = ["${IMAGE_NAME}:policy"]

  args = {
    REMOTE_REPO_URL      = "https://github.com/emma-simbot/policy"
    IMAGE_BASE_NAME      = "${IMAGE_NAME}"
    TORCH_VERISON_SUFFIX = "${TORCH_VERISON_SUFFIX}"
  }
}

target "emma-full" {
  dockerfile = "docker/emma-full.Dockerfile"
  tags       = ["${IMAGE_NAME}:full"]

  args = {
    IMAGE_BASE_NAME = "${IMAGE_NAME}"
  }
}

target "emma-api" {
  dockerfile = "docker/emma-api.Dockerfile"
  tags       = ["${IMAGE_NAME}:api"]

  args = {
    IMAGE_BASE_NAME = "${IMAGE_NAME}"
  }
}

from typing import Literal

import boto3
from fastapi import FastAPI, Request, Response, status
from loguru import Contextualizer, logger

from emma_experience_hub.api.controllers import SimBotController
from emma_experience_hub.common.settings import SimBotSettings
from emma_experience_hub.datamodels.simbot import SimBotRequest, SimBotResponse


app = FastAPI(title="SimBot Challenge Inference")

state: dict[Literal["controller"], SimBotController] = {}


def _create_logger_context(request: SimBotRequest) -> Contextualizer:
    """Contextualise the logger for the current request."""
    return logger.contextualize(
        session_id=request.header.session_id,
        prediction_request_id=request.header.prediction_request_id,
    )


@app.on_event("startup")
async def startup_event() -> None:
    """Handle the startup of the API."""
    simbot_settings = SimBotSettings.from_env()
    boto3.setup_default_session(profile_name=simbot_settings.aws_profile)

    controller = SimBotController.from_simbot_settings(simbot_settings)

    # Check clients every 15 seconds for 100 attempts (=1500s=25mins), which is ridiculously long
    # because ECR can take up to 300secs to download all the images
    if not controller.healthcheck(attempts=100, interval=15):  # noqa: WPS432
        raise AssertionError("Clients failed to respond to healthchecks.")

    state["controller"] = controller

    logger.info("API for the SimBot Arena is ready.")


@app.get("/ping", status_code=status.HTTP_200_OK)
@app.get("/healthcheck", status_code=status.HTTP_200_OK)
async def healthcheck(response: Response) -> str:
    """Perform a healthcheck across all the clients."""
    try:
        state["controller"].healthcheck()
    except Exception as err:
        logger.error("The API is not currently healthy", exc_info=err)
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return "failed"

    return "success"


@app.post("/v1/predict", response_model=SimBotResponse)
async def handle_request_from_simbot_arena(request: Request, response: Response) -> SimBotResponse:
    """Handle a new request from the SimBot API."""
    raw_request = await request.json()

    # Parse the request from the server
    try:
        simbot_request = SimBotRequest.parse_obj(raw_request)
    except Exception as request_err:
        logger.exception("Unable to parse request", exc_info=request_err)
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        raise request_err

    # Verify the state is healthy
    try:
        state["controller"].healthcheck()
    except Exception as state_err:
        logger.exception("Clients are not currently healthy", exc_info=state_err)
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        raise state_err

    with _create_logger_context(simbot_request):
        # Log the incoming request
        logger.info(f"Received request: {simbot_request.json(by_alias=True)}")

        # Handle the request
        simbot_response = state["controller"].handle_request_from_simbot_arena(simbot_request)

        # Return response
        logger.info(f"Returning the response {simbot_response.json(by_alias=True)}")
        return simbot_response

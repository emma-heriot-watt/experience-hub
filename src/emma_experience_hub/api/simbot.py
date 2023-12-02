from typing import Literal

from fastapi import BackgroundTasks, FastAPI, Request, Response, status
from loguru import logger

from emma_experience_hub.api.controllers import SimBotController
from emma_experience_hub.api.observability import create_logger_context
from emma_experience_hub.common.settings import SimBotSettings
from emma_experience_hub.datamodels.simbot import SimBotRequest, SimBotResponse


app = FastAPI(title="SimBot Challenge Inference")


state: dict[Literal["controller"], SimBotController] = {}


@app.on_event("startup")
async def startup_event() -> None:
    """Handle the startup of the API."""
    simbot_settings = SimBotSettings.from_env()
    # boto3.setup_default_session(profile_name=simbot_settings.aws_profile)

    state["controller"] = SimBotController.from_simbot_settings(simbot_settings)

    logger.info("API for the SimBot Arena is ready.")


@app.get("/ping", status_code=status.HTTP_200_OK)
@app.get("/healthcheck", status_code=status.HTTP_200_OK)
async def healthcheck(response: Response) -> str:
    """Perform a healthcheck across all the clients."""
    try:
        healthcheck_result = state["controller"].healthcheck()
    except Exception:
        logger.exception("The API is not currently healthy")
        healthcheck_result = False

    if not healthcheck_result:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return "failed"

    return "success"


@app.post("/v1/predict")
async def handle_request_from_simbot_arena(
    request: Request, response: Response, background_tasks: BackgroundTasks
) -> SimBotResponse:
    """Handle a new request from the SimBot API."""
    raw_request = await request.json()

    # Parse the request from the server
    try:
        simbot_request = SimBotRequest.parse_obj(raw_request)
    except Exception as request_err:
        logger.exception("Unable to parse request")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        raise request_err

    with create_logger_context(simbot_request):
        # Log the incoming request
        logger.info(f"Received request: {raw_request}")

        # Handle the request
        simbot_response = state["controller"].handle_request_from_simbot_arena(simbot_request)

        # Return response
        logger.info(f"Returning the response {simbot_response.json(by_alias=True)}")
        return simbot_response

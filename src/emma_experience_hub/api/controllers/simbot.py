import boto3
from fastapi import FastAPI, Request, Response, status
from loguru import logger
from uvicorn import Config, Server

from emma_experience_hub.api.state.simbot import (
    SimBotControllerClients,
    SimBotControllerPipelines,
    SimBotControllerState,
)
from emma_experience_hub.common.logging import setup_logging
from emma_experience_hub.common.settings import Settings, SimBotSettings
from emma_experience_hub.datamodels.simbot import SimBotRequest
from emma_experience_hub.datamodels.simbot.response import SimBotResponse


settings = Settings.from_env()
simbot_settings = SimBotSettings.from_env()


app = FastAPI()

# Create an empty version of the state that will not error massively on module load
state: SimBotControllerState = SimBotControllerState.construct()  # type: ignore[call-arg]


@app.on_event("startup")
async def startup_event() -> None:
    """Handle the startup of the API."""
    boto3.setup_default_session(profile_name=settings.aws_profile)

    clients = SimBotControllerClients.from_simbot_settings(simbot_settings)
    pipelines = SimBotControllerPipelines.from_controller_clients(clients, simbot_settings)

    if not clients.healthcheck():
        # TODO: What to do here?
        raise NotImplementedError

    state.settings = simbot_settings
    state.clients = clients
    state.pipelines = pipelines

    logger.info("API for the SimBot Arena is ready.")


@app.get("/ping", status_code=status.HTTP_200_OK)
@app.get("/healthcheck", status_code=status.HTTP_200_OK)
async def healthcheck(response: Response) -> str:
    """Perform a healthcheck across all the clients."""
    try:
        state.healthcheck()
    except Exception as err:
        logger.exception("The API is not currently healthy", exc_info=err)
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return "failed"

    return "success"


@app.post("/v1/predict", response_model=SimBotResponse)
async def handle_request_from_simbot_arena(request: Request, response: Response) -> SimBotResponse:
    """Handle a new request from the SimBot API."""
    raw_request = await request.json()

    logger.debug(f"Received request {raw_request}")
    # Parse the request from the server
    try:
        simbot_request = SimBotRequest.parse_obj(raw_request)
    except Exception as request_err:
        logger.exception("Unable to parse request", exc_info=request_err)
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        raise request_err

    # Verify the state is healthy
    try:
        state.healthcheck()
    except Exception as state_err:
        logger.exception("Clients are not currently healthy", exc_info=state_err)
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        raise state_err

    # Run the entire pipeline
    logger.debug("Running request processing")
    session = state.pipelines.request_processing.run(simbot_request)

    if session.current_turn.speech:
        logger.debug(f"Incoming utterance: `{session.current_turn.speech.utterance}`")

    logger.debug("Running NLU")
    session = state.pipelines.nlu.run(session)
    logger.debug(f"Current intent: `{session.current_turn.intent}`")

    logger.debug("Running response generation")
    session = state.pipelines.response_generation.run(session)
    logger.debug(f"Raw output response: `{session.current_turn.raw_output}`")

    # Send the new session turn to the server
    state.clients.session_db.add_session_turn(session.current_turn)

    # Convert the turn to the response
    simbot_response = session.current_turn.convert_to_simbot_response()

    logger.debug(f"Returning the response {simbot_response.json(by_alias=True)}")

    return simbot_response


if __name__ == "__main__":
    server = Server(
        Config(
            "emma_experience_hub.api.controllers.simbot:app",
            host=simbot_settings.host,
            port=simbot_settings.port,
        ),
    )
    setup_logging()
    server.run()

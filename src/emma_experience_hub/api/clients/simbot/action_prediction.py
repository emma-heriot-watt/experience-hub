from emma_experience_hub.api.clients.emma_policy import EmmaPolicyClient
from emma_experience_hub.datamodels import DialogueUtterance, EnvironmentStateTurn


class SimbotActionPredictionClient(EmmaPolicyClient):
    """Action prediction client which interfaces with the Policy model."""

    def get_visual_token(
        self,
        environment_state_history: list[EnvironmentStateTurn],
        dialogue_history: list[DialogueUtterance],
    ) -> str:
        """Generate a response from the features and provided language."""
        raise NotImplementedError()

        # emma_policy_request = EmmaPolicyRequest(
        #     environment_history=environment_state_history, dialogue_history=dialogue_history
        # )
        # logger.debug(f"Sending {emma_policy_request.num_images} images.")
        # logger.debug(f"Sending dialogue history: {emma_policy_request.dialogue_history}")

        # response = httpx.post(
        #     f"{self._endpoint}/generate",
        #     json=orjson.loads(
        #         emma_policy_request.json(
        #             models_as_dict=True,
        #             exclude={
        #                 "environment_history": {
        #                     "__all__": {"features": {"__all__": {"class_labels"}}}
        #                 }
        #             },
        #         )
        #     ),
        # )

        # try:
        #     response.raise_for_status()
        # except httpx.HTTPError as err:
        #     logger.exception("Unable to get response from EMMA policy server", exc_info=err)
        #     raise err from None

        # return response.json()

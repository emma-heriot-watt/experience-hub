from concurrent.futures import ThreadPoolExecutor

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from loguru import logger

from emma_experience_hub.api.clients.dynamo_db import DynamoDbClient
from emma_experience_hub.datamodels.simbot import SimBotSessionTurn


class SimBotSessionDbClient(DynamoDbClient):
    """Client for storing SimBot session data."""

    primary_key = "session_id"
    sort_key = "idx"
    data_key = "turn"

    def healthcheck(self) -> bool:
        """Verify that the DB can be accessed and that it is ready."""
        dynamodb_client = boto3.client(
            "dynamodb", region_name=self._resource_region  # pyright: ignore
        )

        try:
            dynamodb_client.describe_table(TableName=self._table_name)
        except dynamodb_client.exceptions.ResourceNotFoundException as err:
            logger.exception("Cannot find DynamoDB table", exc_info=err)
            return False

        return True

    def add_session_turn(self, session_turn: SimBotSessionTurn) -> None:
        """Add a session turn to the table."""
        try:
            response = self._table.put_item(
                Item={
                    self.primary_key: session_turn.session_id,
                    self.sort_key: session_turn.idx,
                    self.data_key: session_turn.json(by_alias=True),
                },
                ConditionExpression="attribute_not_exists(#sort_key)",
                ExpressionAttributeNames={"#sort_key": self.sort_key},
            )
            logger.debug(response)
        except ClientError as err:
            error_code = err.response["Error"]["Code"]  # pyright: ignore

            if error_code != "ConditionalCheckFailedException":
                logger.exception("Could not add turn to table.", exc_info=err)
                raise err

    def put_session_turn(self, session_turn: SimBotSessionTurn) -> None:
        """Put a session turn to the table.

        If the turn already exists, it WILL overwrite it.
        """
        try:
            self._table.put_item(
                Item={
                    self.primary_key: session_turn.session_id,
                    self.sort_key: session_turn.idx,
                    self.data_key: session_turn.json(by_alias=True),
                },
            )
        except ClientError as err:
            logger.exception("Could not add turn to table.", exc_info=err)
            raise err

    def get_session_turn(self, session_id: str, idx: int) -> SimBotSessionTurn:
        """Get the session turn from the table."""
        try:
            response = self._table.get_item(Key={self.primary_key: session_id, self.sort_key: idx})
        except ClientError as err:
            logger.exception("Could not get session turn from table", exc_info=err)
            raise err

        return SimBotSessionTurn.parse_obj(response["Item"][self.data_key])

    def get_all_session_turns(self, session_id: str) -> list[SimBotSessionTurn]:
        """Get all the turns for a given session."""
        try:
            response = self._table.query(
                KeyConditionExpression=Key(self.primary_key).eq(session_id)
            )
        except ClientError as query_err:
            logger.exception("Could not query for session turns", exc_info=query_err)
            raise query_err

        with ThreadPoolExecutor() as thread_pool:
            # Try parse everything and hope it doesn't crash
            try:
                parsed_responses = list(
                    thread_pool.map(
                        SimBotSessionTurn.parse_raw,
                        (response_item[self.data_key] for response_item in response["Items"]),
                    )
                )
            except Exception as parse_err:
                logger.exception(
                    "Could not parse session turns from response. Returning an empty list.",
                    exc_info=parse_err,
                )
                return []

        logger.debug(f"Successfully got previous `{len(parsed_responses)}` turns")
        return parsed_responses

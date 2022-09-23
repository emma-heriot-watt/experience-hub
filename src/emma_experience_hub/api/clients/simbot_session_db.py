from datetime import datetime

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from pydantic import parse_obj_as

from emma_experience_hub.common import get_logger
from emma_experience_hub.common.settings import Settings
from emma_experience_hub.datamodels.simbot import SimBotSessionTurn


log = get_logger()

boto3.setup_default_session(profile_name=Settings().aws_profile)


class DynamoDbClient:
    """Base client for connecting to Amazon DynamoDB."""

    primary_key: str
    sort_key: str
    data_key: str

    def __init__(self, resource_region: str, table_name: str) -> None:
        self._resource_region = resource_region
        self._table_name = table_name

        self._db = boto3.resource("dynamodb", self._resource_region)
        self._table = self._db.Table(self._table_name)


class SimBotSessionDbClient(DynamoDbClient):
    """Client for storing SimBot session data."""

    primary_key = "session_id"
    sort_key = "timestamp"
    data_key = "turn"

    def put_session_turn(self, session_turn: SimBotSessionTurn) -> None:
        """Put a session turn to the table.

        If the turn already exist, it WILL overwrite it.
        """
        try:
            self._table.put_item(
                Item={
                    self.primary_key: session_turn.session_id,
                    self.sort_key: str(session_turn.timestamp.start),
                    self.data_key: session_turn.json(),
                }
            )
        except ClientError as err:
            log.exception("Could not add turn to table.", exc_info=err)
            # TODO: Should there be a raise here?
            raise err

    def get_session_turn(self, session_id: str, timestamp: datetime) -> SimBotSessionTurn:
        """Get the session turn from the table."""
        try:
            response = self._table.get_item(
                Key={self.primary_key: session_id, self.sort_key: str(timestamp)}
            )
        except ClientError as err:
            log.exception("Could not get session turn from table", exc_info=err)
            raise err

        return SimBotSessionTurn.parse_obj(response["Item"][self.data_key])

    def get_all_session_turns(self, session_id: str) -> list[SimBotSessionTurn]:
        """Get all the turns for a given session."""
        try:
            response = self._table.query(
                KeyConditionExpression=Key(self.primary_key).eq(session_id)
            )
        except ClientError as err:
            log.exception("Could not query for session turns", exc_info=err)
            # TODO: Should there be a raise here?
            raise err

        return parse_obj_as(list[SimBotSessionTurn], response["Items"])

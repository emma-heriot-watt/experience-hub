import boto3

from emma_experience_hub.api.clients.client import Client


class DynamoDbClient(Client):
    """Base client for connecting to Amazon DynamoDB."""

    primary_key: str
    sort_key: str
    data_key: str

    def __init__(self, resource_region: str, table_name: str) -> None:
        self._resource_region = resource_region
        self._table_name = table_name

        self._db = boto3.resource("dynamodb", self._resource_region)
        self._table = self._db.Table(self._table_name)

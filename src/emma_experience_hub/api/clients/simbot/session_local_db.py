from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import sqlite3
from loguru import logger

from emma_experience_hub.api.clients.client import Client
from emma_experience_hub.datamodels.simbot import SimBotSessionTurn


class SimBotSQLLiteClient:
    """Local Client for storing SimBot session data."""

    primary_key: str
    sort_key: str
    data_key: str

    def __init__(self, db_file: Path) -> None:
        self._db_file = db_file
        self.create_table()

    def create_table(self) -> None:  # noqa: WPS231
        """Create table."""
        if self._db_file.exists():
            return

        try:  # noqa: WPS229
            connection = sqlite3.connect(self._db_file)
            sqlite_create_table_query = """CREATE TABLE session_table (
                                        primary_key TEXT NOT NULL,
                                        sort_key INTEGER NOT NULL,
                                        data_key TEXT NOT NULL,
                                        PRIMARY KEY (primary_key, sort_key)
                                        );"""

            cursor = connection.cursor()
            cursor.execute(sqlite_create_table_query)
            connection.commit()
            logger.info("SQLite table created")

            cursor.close()

        except sqlite3.Error as error:
            logger.exception("Error while creating a sqlite table", error)
        finally:
            if connection:
                connection.close()

    def healthcheck(self) -> bool:
        """Verify that the DB can be accessed and that it is ready."""
        try:
            sqlite3.connect(self._db_file)
        except Exception:
            logger.exception("Cannot find db table")
            return False

        return True

    def add_session_turn(self, session_turn: SimBotSessionTurn) -> None:
        """Add a session turn to the table."""
        try:  # noqa: WPS229
            connection = sqlite3.connect(self._db_file)
            cursor = connection.cursor()

            sqlite_insert_with_param = """INSERT OR REPLACE INTO session_table
                                (primary_key, sort_key, data_key)
                                VALUES (?, ?, ?);"""

            data_tuple = (
                session_turn.session_id,
                session_turn.idx,
                session_turn.json(by_alias=True),
            )
            cursor.execute(sqlite_insert_with_param, data_tuple)
            connection.commit()
            logger.info("Successfully inserted turn into table")

            cursor.close()

        except sqlite3.Error as error:
            logger.exception("Failed to insert turn into table")
            raise error
        finally:
            if connection:
                connection.close()

    def put_session_turn(self, session_turn: SimBotSessionTurn) -> None:
        """Put a session turn to the table.

        If the turn already exists, it WILL overwrite it.
        """
        self.add_session_turn(session_turn)

    def get_session_turn(self, session_id: str, idx: int) -> SimBotSessionTurn:
        """Get the session turn from the table."""
        try:  # noqa: WPS229
            connection = sqlite3.connect(self._db_file)
            cursor = connection.cursor()

            sql_select_query = "select * from session_table where primary_key = ? and sort_key = ?"
            cursor.execute(sql_select_query, (session_id, idx))
            turn = cursor.fetchone()
            cursor.close()

        except sqlite3.Error as error:
            logger.exception("Failed to read data from table")
            raise error
        finally:
            if connection:
                connection.close()

        return SimBotSessionTurn.parse_raw(turn[2])

    def get_all_session_turns(self, session_id: str) -> list[SimBotSessionTurn]:
        """Get all the turns for a given session."""
        try:
            all_raw_turns = self._get_all_session_turns(session_id)
        except Exception as query_err:
            logger.exception("Could not query for session turns")
            raise query_err

        with ThreadPoolExecutor() as thread_pool:
            # Try parse everything and hope it doesn't crash
            try:
                parsed_responses = list(
                    thread_pool.map(
                        SimBotSessionTurn.parse_raw,
                        (response_item[2] for response_item in all_raw_turns),
                    )
                )
            except Exception:
                logger.exception(
                    "Could not parse session turns from response. Returning an empty list."
                )
                return []

        logger.debug(f"Successfully got previous `{len(parsed_responses)}` turns")

        # Sort the responses by the sort key before returning
        sorted_responses = sorted(parsed_responses, key=lambda turn: turn.idx)

        return sorted_responses

    def _get_all_session_turns(self, session_id: str) -> list[tuple[str, int, str]]:
        try:  # noqa: WPS229
            connection = sqlite3.connect(self._db_file)
            cursor = connection.cursor()

            sql_select_query = (
                "select * from session_table where primary_key = ? ORDER BY sort_key"
            )
            cursor.execute(sql_select_query, (session_id,))
            turns = cursor.fetchall()
            cursor.close()

        except sqlite3.Error as error:
            logger.exception("Failed to read data from table")
            raise error
        finally:
            if connection:
                connection.close()

        return turns


# db = SimBotSQLLiteClient(
#     Path("/home/gmp2000/simbot-offline-inference/storage/experience-hub/storage/local_sessions.db")
# )

# session_turns = db.get_all_session_turns("T1_39786908-bee2-48a5-bf33-6640de5b80e8")

# for turn in session_turns:
#     print(turn.prediction_request_id)
#     if turn.speech:
#         print(turn.speech.original_utterance.utterance, turn.speech.modified_utterance.utterance)
#     print(turn.actions.interaction.raw_output)
#     if turn.actions.interaction.status:
#         print(turn.actions.interaction.status.success)
# breakpoint()

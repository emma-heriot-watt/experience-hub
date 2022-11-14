from pytest_cases import parametrize

from emma_experience_hub.constants.alexa import ALEXA_WAKE_WORDS
from emma_experience_hub.datamodels.simbot.payloads import SimBotSpeechRecognitionPayload


@parametrize("utterance", ["turn left", "turn on the computer", "goto the computer"])
@parametrize("num_repeated_wake_words", [1, 2, 3], idgen="{num_repeated_wake_words}_wake_word")
@parametrize("wake_word", ALEXA_WAKE_WORDS)
def test_alexa_wake_words_are_removed_from_speech_recognition_utterance(
    utterance: str, num_repeated_wake_words: int, wake_word: str
) -> None:
    payload_utterance = utterance

    # Prepend the wake words to the start
    for _ in range(num_repeated_wake_words):
        payload_utterance = f"{wake_word} {payload_utterance}"

    payload = SimBotSpeechRecognitionPayload.parse_obj(
        {
            "tokens": [
                {"value": token, "confidence": {"score": 0.9, "bin": "HIGH"}}
                for token in payload_utterance.split(" ")
            ]
        }
    )
    assert payload.utterance == utterance

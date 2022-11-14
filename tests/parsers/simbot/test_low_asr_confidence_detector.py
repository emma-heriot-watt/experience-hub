from pytest_cases import parametrize, parametrize_with_cases

from emma_experience_hub.datamodels.simbot.payloads import SimBotSpeechRecognitionPayload
from emma_experience_hub.parsers.simbot.low_asr_confidence_detector import (
    SimBotLowASRConfidenceDetector,
)


class SimBotASROutputCases:
    def case_high_confidence(self) -> SimBotSpeechRecognitionPayload:
        return SimBotSpeechRecognitionPayload.parse_obj(
            {
                "tokens": [
                    {"value": "go", "confidence": {"score": 0.729, "bin": "HIGH"}},
                    {"value": "to", "confidence": {"score": 0.844, "bin": "HIGH"}},
                    {"value": "the", "confidence": {"score": 0.711, "bin": "HIGH"}},
                    {"value": "sink", "confidence": {"score": 0.315, "bin": "HIGH"}},
                ]
            }
        )

    def case_very_low_confidence(self) -> SimBotSpeechRecognitionPayload:
        return SimBotSpeechRecognitionPayload.parse_obj(
            {
                "tokens": [
                    {"value": "laforce", "confidence": {"score": 0.153, "bin": "HIGH"}},
                ]
            }
        )

    def case_just_below_half_confidence(self) -> SimBotSpeechRecognitionPayload:
        return SimBotSpeechRecognitionPayload.parse_obj(
            {
                "tokens": [
                    {"value": "laforce", "confidence": {"score": 0.49999, "bin": "HIGH"}},
                ]
            }
        )

    def case_just_above_half_confidence(self) -> SimBotSpeechRecognitionPayload:
        return SimBotSpeechRecognitionPayload.parse_obj(
            {
                "tokens": [
                    {"value": "laforce", "confidence": {"score": 0.5000001, "bin": "HIGH"}},
                ]
            }
        )

    def case_with_no_tokens(self) -> SimBotSpeechRecognitionPayload:
        return SimBotSpeechRecognitionPayload.parse_obj({"tokens": []})


@parametrize_with_cases("payload", cases=SimBotASROutputCases)
@parametrize("threshold", [0.1, 0.3, 0.5, 0.7], idgen="threshold={threshold}")
def test_simbot_low_asr_confidence_detector(
    payload: SimBotSpeechRecognitionPayload, threshold: float
) -> None:
    asr_filter = SimBotLowASRConfidenceDetector(threshold)

    if payload.tokens:
        average_score = asr_filter._get_average_confidence_score(payload.all_confidence_scores)
        is_above_threshold = asr_filter(payload)

        assert is_above_threshold == (average_score > threshold)
    else:
        assert not asr_filter(payload)

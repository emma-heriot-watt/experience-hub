from emma_experience_hub.datamodels.simbot.payloads import SimBotObjectOutputType


def test_object_output_type_defaults_to_mask() -> None:
    assert SimBotObjectOutputType.default() == SimBotObjectOutputType.object_mask


def test_object_output_type_for_sticky_note_is_class() -> None:
    entity_name = "sticky note"
    assert SimBotObjectOutputType.get_type_from_args(entity_name)

import itertools
from typing import Optional

import torch
from hypothesis import assume, strategies as st

from emma_experience_hub.constants.simbot import (
    get_simbot_object_id_to_class_name_map,
    get_simbot_object_label_to_class_name_map,
    get_simbot_room_names,
)
from emma_experience_hub.datamodels import EmmaExtractedFeatures
from emma_experience_hub.datamodels.simbot import (
    SimBotAction,
    SimBotActionStatus,
    SimBotActionStatusType,
    SimBotActionType,
    SimBotDialogAction,
    SimBotIntent,
    SimBotIntentType,
    SimBotSession,
    SimBotSessionState,
    SimBotSessionTurn,
    SimBotSessionTurnActions,
    SimBotSessionTurnIntent,
)
from emma_experience_hub.datamodels.simbot.payloads import (
    SimBotAuxiliaryMetadataPayload,
    SimBotDialogPayload,
    SimBotGotoObject,
    SimBotGotoPayload,
    SimBotGotoRoom,
    SimBotInteractionObject,
    SimBotNavigationPayload,
    SimBotObjectInteractionPayload,
    SimBotPayload,
)


@st.composite
def simbot_room_names(draw: st.DrawFn) -> str:
    """Get a room name for the arena."""
    return draw(
        st.sampled_from(
            list(itertools.chain(get_simbot_room_names(), get_simbot_room_names(lowercase=True)))
        )
    )


@st.composite
def simbot_object_labels(draw: st.DrawFn) -> str:
    """Get one of the class labels."""
    return draw(st.sampled_from(list(get_simbot_object_label_to_class_name_map().keys())))


@st.composite
def simbot_class_names(draw: st.DrawFn) -> str:
    """Get one of the class names for the arena."""
    return draw(st.sampled_from(list(get_simbot_object_id_to_class_name_map().values())))


@st.composite
def simbot_viewpoints(draw: st.DrawFn) -> set[str]:
    """Generate a list of viewpoints."""
    viewpoints = []

    for room_name in list(get_simbot_room_names()):
        room_viewpoint_count = draw(st.integers(0, 10))
        room_viewpoints = [f"{room_name}_{idx}" for idx in range(room_viewpoint_count)]
        viewpoints.extend(room_viewpoints)

    return set(viewpoints)


@st.composite
def simbot_extracted_features(
    draw: st.DrawFn,
    num_frames: st.SearchStrategy[int] = st.integers(1, 4),
    min_num_objects: st.SearchStrategy[int] = st.integers(1, 5),
) -> list[EmmaExtractedFeatures]:
    """Generate a list of dummy extracted features."""
    frames = []

    for _ in range(draw(num_frames)):
        num_objects_in_frame = draw(st.integers(draw(min_num_objects), 36))
        bbox_features = draw(
            st.lists(
                st.lists(st.integers(0, 1000), min_size=3, max_size=3),
                min_size=num_objects_in_frame,
                max_size=num_objects_in_frame,
            )
        )
        bbox_coords = draw(
            st.lists(
                st.lists(st.integers(0, 1000), min_size=4, max_size=4),
                min_size=num_objects_in_frame,
                max_size=num_objects_in_frame,
            )
        )
        bbox_probas = draw(
            st.lists(
                st.lists(st.floats(0, 1), min_size=4, max_size=4),
                min_size=num_objects_in_frame,
                max_size=num_objects_in_frame,
            )
        )
        cnn_features = draw(
            st.lists(
                st.integers(0, 1000), min_size=num_objects_in_frame, max_size=num_objects_in_frame
            ),
        )
        class_labels = draw(
            st.lists(
                simbot_class_names(), min_size=num_objects_in_frame, max_size=num_objects_in_frame
            )
        )
        frames.append(
            EmmaExtractedFeatures(
                bbox_features=torch.tensor(bbox_features),
                bbox_coords=torch.tensor(bbox_coords),
                bbox_probas=torch.tensor(bbox_probas),
                cnn_features=torch.tensor(cnn_features),
                class_labels=class_labels,
                entity_labels=class_labels,
                width=300,
                height=300,
            )
        )

    return frames


@st.composite
def simbot_auxiliary_metadata_payloads(draw: st.DrawFn) -> SimBotAuxiliaryMetadataPayload:
    """Generate an auxiliary metadata payload."""
    return draw(
        st.just(SimBotAuxiliaryMetadataPayload.from_efs_uri("efs://sample-game-metadata.json"))
    )


@st.composite
def simbot_object_interaction_payloads(
    draw: st.DrawFn, class_names: st.SearchStrategy[str] = simbot_class_names()
) -> SimBotObjectInteractionPayload:
    """Generate an object interaction payload."""
    mask = draw(st.lists(st.lists(st.integers(0, 300))))
    color_image_index = draw(st.integers(0, 4))

    return SimBotObjectInteractionPayload(
        object=SimBotInteractionObject(
            name=draw(class_names), colorImageIndex=color_image_index, mask=mask
        )
    )


@st.composite
def simbot_dialog_payloads(draw: st.DrawFn) -> SimBotDialogPayload:
    """Generate a dialog payload."""
    rule_id = draw(st.integers(0, 10))
    return SimBotDialogPayload(value=draw(st.text(min_size=1)), rule_id=rule_id)


@st.composite
def simbot_goto_object_payloads(draw: st.DrawFn) -> SimBotGotoPayload:
    """Generate a payload for going to an object."""
    interaction_payload = draw(simbot_object_interaction_payloads())
    return SimBotGotoPayload(object=SimBotGotoObject.parse_obj(interaction_payload.object.dict()))


@st.composite
def simbot_goto_room_payloads(
    draw: st.DrawFn, room_names: st.SearchStrategy[str] = simbot_room_names()
) -> SimBotGotoPayload:
    """Generate a payload for going to a room."""
    return SimBotGotoPayload(object=SimBotGotoRoom(officeRoom=draw(room_names)))


@st.composite
def simbot_low_level_navigation_payloads(draw: st.DrawFn) -> SimBotNavigationPayload:
    """Generate a payload for a low level navigation action."""
    action_type = draw(st.sampled_from(SimBotActionType.low_level_navigation()))
    assume(
        action_type
        not in {
            SimBotActionType.Move,
            SimBotActionType.Rotate,
            SimBotActionType.Look,
        }
    )
    assert issubclass(action_type.payload_model, SimBotNavigationPayload)
    payload_model: type[SimBotNavigationPayload] = action_type.payload_model
    model = draw(st.builds(payload_model))
    return model


@st.composite
def simbot_interaction_payloads(draw: st.DrawFn) -> SimBotPayload:
    """Generate a payload for an interaction action."""
    return draw(
        st.one_of(
            simbot_low_level_navigation_payloads(),
            simbot_goto_room_payloads(),
            simbot_goto_object_payloads(),
        )
    )


@st.composite
def simbot_action_payloads(draw: st.DrawFn) -> SimBotPayload:
    """Randomly pick and build a payload model."""
    return draw(
        st.one_of(
            simbot_low_level_navigation_payloads(),
            simbot_goto_room_payloads(),
            simbot_goto_object_payloads(),
            simbot_dialog_payloads(),
        )
    )


@st.composite
def simbot_action_status(
    draw: st.DrawFn,
    action_type: st.SearchStrategy[SimBotActionType] = st.sampled_from(SimBotActionType),
    is_action_successful: st.SearchStrategy[bool] = st.booleans(),
) -> SimBotActionStatus:
    """Generate an action status."""
    drawn_action_type = draw(action_type)
    action_status_type = draw(
        st.sampled_from(SimBotActionStatusType).filter(
            lambda error_type: error_type != SimBotActionStatusType.action_successful
        )
    )

    is_success = draw(is_action_successful)

    return draw(
        st.builds(
            SimBotActionStatus,
            type=st.just(drawn_action_type),
            success=st.just(is_success),
            error_type=st.just(action_status_type),
        )
    )


@st.composite
def simbot_actions(
    draw: st.DrawFn,
    payloads: st.SearchStrategy[SimBotPayload] = simbot_action_payloads(),
    include_status: st.SearchStrategy[bool] = st.booleans(),
    is_action_successful: st.SearchStrategy[bool] = st.booleans(),
    allow_none: bool = False,
) -> Optional[SimBotAction]:
    """Randomly create valid SimBot actions."""
    payload = draw(payloads)
    action_type = SimBotActionType.from_payload_model(payload)

    action_status = draw(
        simbot_action_status(
            action_type=st.just(action_type), is_action_successful=is_action_successful
        )
    )
    if draw(is_action_successful):
        assume(action_status.error_type)

    action_builder: st.SearchStrategy[SimBotAction] = st.builds(
        SimBotDialogAction if isinstance(payload, SimBotDialogPayload) else SimBotAction,
        id=st.just(0),
        payload=st.just(payload),
        type=st.just(action_type),
        status=st.just(action_status) if draw(include_status) else st.none(),
    )

    if allow_none:
        return draw(st.one_of(action_builder, st.none()))

    return draw(action_builder)


@st.composite
def simbot_session_turns(
    draw: st.DrawFn,
    current_room: st.SearchStrategy[str] = simbot_room_names(),
    interaction_action: st.SearchStrategy[Optional[SimBotAction]] = simbot_actions(
        simbot_interaction_payloads(), allow_none=True
    ),
    dialog_action: st.SearchStrategy[Optional[SimBotDialogAction]] = simbot_actions(  # type: ignore[assignment]
        simbot_dialog_payloads(), allow_none=True
    ),
) -> SimBotSessionTurn:
    """Generate a session turn."""
    session_id = "amzn1.echo-api.session.3f55df67-01ac-48ad-aa5b-380dcd22b837_5"
    intents = SimBotSessionTurnIntent(
        user=None,
        environment=None,
        physical_interaction=SimBotIntent(type=SimBotIntentType.act_one_match),
    )
    drawn_dialog_action = draw(dialog_action)

    actions = SimBotSessionTurnActions(
        interaction=draw(interaction_action), dialog=drawn_dialog_action
    )
    state = SimBotSessionState()
    turn: SimBotSessionTurn = draw(
        st.builds(
            SimBotSessionTurn,
            session_id=st.just(session_id),
            current_room=current_room,
            unique_room_names=st.just(set(get_simbot_room_names())),
            intent=st.just(intents),
            actions=st.just(actions),
            state=st.just(state),
            auxiliary_metadata_uri=st.just(draw(simbot_auxiliary_metadata_payloads()).uri),
        )
    )
    return turn


@st.composite
def simbot_session(
    draw: st.DrawFn,
) -> SimBotSession:
    """Generate a session."""
    session_id = "amzn1.echo-api.session.3f55df67-01ac-48ad-aa5b-380dcd22b837_5"
    session_turns = st.lists(simbot_session_turns(), min_size=1, max_size=5)
    session: SimBotSession = draw(
        st.builds(SimBotSession, session_id=st.just(session_id), turns=session_turns)
    )
    return session

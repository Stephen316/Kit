from dataclasses import dataclass as Dataclass
from typing import Literal, TypedDict

from convert.adapters.solidworks.Resolved.BossEntry import OpNode
from convert.adapters.solidworks.Resolved.Cut.CutOpRead import CutEnd
from convert.adapters.solidworks.Resolved.Cut.CutResultFace import CutResultId
from convert.adapters.solidworks.Resolved.FaceIdentity import FaceHeader, KSurfaceId


# a scope surface can select a boss only through its reached archive identity
@Dataclass(frozen=True, slots=True)
class ScopeOwner:
    BodyId: int
    FileObject: int
    FeatureId: int
    ClockWord: int
    TransferObject: int
    CapClass: str
    EdgeClass: str
    CapEdges: tuple[int, ...]
    CentreAndScale: tuple[float, ...]

    # repeated saved references must agree on document feature and native clock
    @property
    def SurfaceOwner(self) -> tuple[int, int, int]:
        return self.FileObject, self.FeatureId, self.ClockWord


# both body lists preserve raw tail words alongside independently bound ownership
class ScopeBody(TypedDict):
    offset: int
    end: int
    object_index: int
    body_id: int
    feature_id: int
    raw_owner_word: int
    recent_atom_id: int
    raw_terminal_word: int
    unit_component: int
    part_object: int
    face: FaceHeader
    surfaces: list[KSurfaceId | CutResultId]


# absent arrays remain distinct from a present selection even if another list names bodies
class ScopeBodyList(TypedDict):
    offset: int
    end: int
    present: bool
    bodies: tuple[ScopeBody, ...]


# result faces may retain cut sides even when a body was excluded from the cut
class ScopeChoiceFace(FaceHeader):
    end: int
    surfaces: list[KSurfaceId | CutResultId]


# chooser fields remain separate from authored selection and physical body results
class ScopeChoice(TypedDict):
    offset: int
    end: int
    object_index: int
    earlier_body_id: int
    faces: tuple[ScopeChoiceFace, ScopeChoiceFace]
    centre_object: int
    centre_and_scale: tuple[float, ...]
    raw_centre_state: tuple[int, ...]


# saved partition pairs supply another body roster without explaining partition state
class ScopePartition(TypedDict):
    offset: int
    end: int
    object_index: int
    raw_state: int
    atom_body_pairs: tuple[tuple[int, ...], ...]


# the two observed routes keep resolved bodies separate from explicit authored selection
class ScopedCut(OpNode):
    scope_kind: Literal["all_bodies", "explicit"]
    scope_body_ids: tuple[int, ...]
    chooser_body_ids: tuple[int, ...]
    scope_word: int
    scope_word_offset: int
    expanded_scope_word: int
    primary_bodies: ScopeBodyList
    later_bodies: ScopeBodyList
    cut_transfers: tuple[int, ...]
    parent_transfers: tuple[int, ...]
    atom_ids: tuple[int, ...]
    choosers: tuple[ScopeChoice, ScopeChoice]
    partition: ScopePartition
    end_specification: CutEnd
    raw_start_words: tuple[int, ...]
    footer_offset: int
    stream_end: int
    next_map_index: int

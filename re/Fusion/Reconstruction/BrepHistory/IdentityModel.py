from dataclasses import dataclass
import math


@dataclass(frozen=True)
class FeatureTag:
    selector: int
    label: str
    operation_ids: tuple[int, ...]


@dataclass(frozen=True)
class SketchLink:
    primary_id: int
    secondary_id: int
    sense: int
    enum_a: int
    enum_b: int

    def __post_init__(self):
        if not 0 <= self.secondary_id < 1 << 64:
            raise ValueError("Sketch secondary identity exceeds unsigned 64-bit range")
        if self.sense not in (0, 1, 4294967295):
            raise ValueError("Unsupported sketch sense")


@dataclass(frozen=True)
class DesignIdentity:
    body_key: int
    operation_id: int
    body_generation_reference: int
    authoring_unix_microseconds: float
    side_face: FeatureTag
    top_face: FeatureTag
    bottom_face: FeatureTag
    top_edge: FeatureTag
    bottom_edge: FeatureTag
    sketch: SketchLink

    def __post_init__(self):
        if self.body_key < 0 or self.operation_id < 0:
            raise ValueError("Body and operation identities must be nonnegative")
        if not math.isfinite(self.authoring_unix_microseconds):
            raise ValueError("Authoring timestamp must be finite")


@dataclass(frozen=True)
class HistoryIdentity:
    current_state_id: int
    initial_state_id: int
    stream_current_state_id: int
    next_entity_tag: int
    board_status: int
    max_state_id: int | None = None

    def __post_init__(self):
        if not 0 <= self.initial_state_id < self.current_state_id:
            raise ValueError("History state identities must be ordered and nonnegative")
        maximum = self.stream_current_state_id if self.max_state_id is None else self.max_state_id
        object.__setattr__(self, "max_state_id", maximum)
        if not 0 <= self.stream_current_state_id <= maximum < 1 << 31:
            raise ValueError("History current/maximum state identities are invalid")
        if not 0 <= self.next_entity_tag < 1 << 31 or self.board_status not in range(4):
            raise ValueError("History entity tag or board status is invalid")


@dataclass(frozen=True)
class StreamProvenance:
    product: str
    version: str
    saved_at: str
    binary_scale_metadata: float

    def __post_init__(self):
        for value in (self.product, self.version, self.saved_at):
            if not value or not value.isprintable() or len(value.encode()) > 255:
                raise ValueError("Invalid binary header provenance")
        if not math.isfinite(self.binary_scale_metadata):
            raise ValueError("Binary scale metadata must be finite")

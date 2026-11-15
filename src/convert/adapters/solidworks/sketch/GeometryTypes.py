from typing import TypeAlias, TypedDict

# archived points are referenced by their local slot and their saved member identity
KPointId: TypeAlias = tuple[int, int]

# point parsing carries the relation tally separately from the local coordinate values
KPointRow: TypeAlias = tuple[int, int, tuple[float, ...]]

# line rows keep serialized member and endpoint identities for later region binding
KLineRow: TypeAlias = tuple[int, int, int, int, int]

# the extra handle fields determine whether its member belongs to this sketch
KEntityHandle: TypeAlias = tuple[int, int, int]

# the dimension parameter and both operands are needed before projecting a distance
KDistanceRow: TypeAlias = tuple[str, int, str, float, int, int]

# the saved axis relation needs a typed line handle and its own record span
KRelationRow: TypeAlias = tuple[int, int, int, int, tuple[int, ...]]


# external references must preserve the feature and entity identities they resolve
class SketchReference(TypedDict):
    feature_id: int
    feature_time: int
    handle_class: str
    handle_fields: KEntityHandle


# inline point references must retain the local proxy identity beside their target
class PointReference(SketchReference):
    local_id: KPointId


# relation counts can be corroborated against the saved point identity
class PointTally(TypedDict):
    id: KPointId
    tally: int


# a saved line keeps its endpoints in sketch coordinates until support is resolved
class SketchLine(TypedDict):
    member_index: int
    native_id: int
    flags: int
    point_indices: list[int]


# a driving value needs both native point operands rather than a positional guess
KSketchDistance = TypedDict(
    "KSketchDistance",
    {
        "class": str,
        "native_id": int,
        "name": str,
        "metres": float,
        "point_handle_objects": list[int],
        "point_native_ids": list[KPointId],
    },
)


# one member axis relations must retain the proven segment target
class SketchRelation(TypedDict):
    start: int
    end: int
    line_handle_object: int
    line_handle_fields: KEntityHandle
    segment_native_id: int
    type_code: int
    kind: str
    scalar_fields: tuple[int, ...]


# logical coincidence state determines whether two archived targets participate
class Coincidence(TypedDict):
    offset: int
    end: int
    type_code: int
    suppressed: bool
    deleted: bool
    point_handle_objects: list[int]
    point_indices: list[int]
    point_native_ids: list[KPointId]


# resolved profiles consume sketch data and map identity before applying their own support
class SketchGeometry(TypedDict):
    object_index: int
    body_start: int
    geometry_end: int
    next_map_index: int
    points_metres: list[tuple[float, ...]]
    point_relation_tallies: list[PointTally]
    external_point_references: list[PointReference]
    lines: list[SketchLine]
    length_dimensions: list[KSketchDistance]
    member_relations: list[SketchRelation]

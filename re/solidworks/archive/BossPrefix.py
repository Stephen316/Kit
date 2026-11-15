"""Read the P04 blind boss through the typed opening of its end specification."""

from convert.adapters.solidworks.container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    KObjectRefKind,
    ReadTag,
)
from BossChooser import read_boss_choosers
from SketchRoot import Require
from SupportPlane import read_feature_base, read_partition_tail


# the optional end objects must be absent to read the witnessed blind controls
def read_blind_end_prefix(cursor):
    offset = cursor.position
    spec = cursor.pointer(KDefinitionKind, "moEndSpec_c")
    cursor.null()
    single_end, flip, direction = cursor.read("<3i")
    Require((single_end, flip, direction), (1, 0, 0), "witnessed boss direction")
    cursor.null()
    conditions = cursor.read("<2i")
    Require(conditions, (0, 0), "witnessed blind end conditions")
    display = ReadTag(cursor.blob, cursor.position)
    Require(display.kind, KClassRefKind, "existing depth dimension class")
    Require(
        cursor.classes.get(display.index),
        "moDisplayDistanceDim_c",
        "typed depth dimension boundary",
    )
    return {
        "offset": offset,
        "object_index": spec,
        "single_end": single_end,
        "flip": flip,
        "direction": direction,
        "conditions": conditions,
        "depth_dimension_offset": cursor.position,
        "depth_dimension_class": display.index,
    }


# the atom references the earlier configuration graph before materializing its own choosers
def read_boss_prefix(cursor, boss):
    read_feature_base(cursor)
    Require(cursor.read("<i3H"), (0, 0, 0, 0), "guarded boss model and atom fields")
    Require(cursor.read("<iH"), (1, 1), "one saved transfer object")
    transferred = cursor.pointer(KObjectRefKind, "moAtom_c")
    Require(cursor.read("<i"), (0,), "empty secondary transfer array")
    cursor.null()
    Require(cursor.read("<5i"), (1, 101, 3, 0, 1), "guarded boss atom arrays and mode")
    choosers = read_boss_choosers(cursor, boss)
    Require(cursor.read("<H3i"), (0, 0, 0, 1), "guarded boss partition selection")
    marker = cursor.pointer(KClassRefKind, "moPMarkRecord_c")
    (marker_state,) = cursor.read("<i")
    read_partition_tail(cursor)
    atom_end = cursor.position
    cursor.null()
    cursor.null()
    Require(cursor.read("<Hi"), (0, 0), "empty modern body feature tail")
    specification = read_blind_end_prefix(cursor)
    return {
        **boss,
        "transfer_object": transferred,
        "choosers": choosers,
        "partition_object": marker,
        "partition_state": marker_state,
        "atom_end": atom_end,
        "end_specification": specification,
    }


# the nested depth display and from end record must both return before the next feature
def read_boss_close(cursor):
    from DepthDisplay import read_depth_display

    depth = read_depth_display(cursor)
    cursor.null()
    Require(
        cursor.read("<BHBHd6i"),
        (1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0),
        "guarded empty end surface and draft fields",
    )
    cursor.null()
    cursor.null()
    Require(cursor.read("<4i2H3i"), (0,) * 9, "guarded blind end feature fields")
    origin = cursor.pointer(KDefinitionKind, "moFromEndSpec_c")
    Require(cursor.read("<i"), (0,), "blind boss starts from its sketch plane")
    cursor.read("<5i")
    Require(cursor.read("<di"), (0, -1), "guarded extrusion return state")
    return {"depth_display": depth, "from_end_object": origin, "end": cursor.position}

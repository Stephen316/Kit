"""Read the P04 cut operation and the resolved list footer."""

from BossPrefix import read_body_feature_tail, read_end_prefix, read_end_tail
from convert.adapters.solidworks.container.Archive import KClassRefKind, KObjectRefKind
from CutChooser import read_cut_choosers, read_cut_solid
from DepthDisplay import read_depth_display
from SketchRoot import Require
from SupportPlane import read_feature_base, read_partition_tail


# the stored end condition determines whether the cut owns a depth parameter
def read_cut_end(cursor):
    specification = read_end_prefix(cursor, KClassRefKind)
    conditions = specification["conditions"]
    Require(conditions in ((0, 0), (1, 0)), True, "witnessed cut end conditions")
    depth = None
    if conditions[0] == 0:
        depth = read_depth_display(cursor, KClassRefKind)
    else:
        cursor.null()
    origin = read_end_tail(cursor, KClassRefKind, 1)
    Require(cursor.read("<di"), (0, 1), "guarded cut feature return")
    return {
        **specification,
        "depth_display": depth,
        "from_end_object": origin,
        "end": cursor.position,
    }


# the cut retains its own transfer and the boss transfer before loading the result body
def read_cut_operation(cursor, cut, boss):
    read_feature_base(cursor)
    Require(cursor.read("<i3H"), (0, 0, 0, 0), "guarded cut model and atom fields")
    Require(cursor.read("<iH"), (1, 1), "one saved cut transfer")
    transfer = cursor.pointer(KObjectRefKind, "moAtom_c")
    Require(transfer != boss["transfer_object"], True, "distinct cut transfer")
    Require(cursor.read("<iH"), (1, 1), "one parent boss transfer")
    parent = cursor.pointer(KObjectRefKind, "moAtom_c")
    Require(parent, boss["transfer_object"], "cut refers to the earlier boss transfer")
    cursor.null()
    count, atom_id, mode, presence, items = cursor.read("<4iH")
    Require((count, mode, presence, items), (1, 3, 1, 1), "one guarded cut result body")
    body = read_cut_solid(cursor, boss, cut)
    choosers = read_cut_choosers(cursor, boss, cut)
    Require(cursor.read("<H3i"), (0, 0, 0, 1), "guarded cut partition selection")
    marker = cursor.pointer(KClassRefKind, "moPMarkRecord_c")
    (state,) = cursor.read("<i")
    read_partition_tail(cursor)
    atom_end = cursor.position
    read_body_feature_tail(cursor)
    specification = read_cut_end(cursor)
    Require(cursor.read("<i"), (0,), "resolved list footer")
    Require(cursor.position, len(cursor.blob), "complete resolved list extent")
    return {
        **cut,
        "transfer_object": transfer,
        "parent_transfer_object": parent,
        "atom_id": atom_id,
        "solid_body": body,
        "choosers": choosers,
        "partition_object": marker,
        "partition_state": state,
        "atom_end": atom_end,
        "end_specification": specification,
    }


# independent readback checks the cut placement termination and physical depth separately
def check_cut_operation(prefix, measured, sketch):
    transform = prefix["cut_profile"]["placement"]
    basis = transform["basis"] or (1, 0, 0, 0, 1, 0, 0, 0, 1)
    Require(
        (*basis, *transform["translation_scale"]),
        tuple(sketch["model_to_sketch_transform"][:13]),
        "measured cut placement",
    )
    cut = prefix["cut_operation"]
    matches = [
        feature
        for feature in measured["feature_tree"]
        if (feature["type"], feature["name"]) == ("ICE", cut["name"])
    ]
    Require(len(matches), 1, "one independently measured cut operation")
    feature = matches[0]
    operation = feature["operation"]
    spec = cut["end_specification"]
    Require(
        (spec["single_end"] == 0, spec["direction"] != 0, spec["conditions"][0]),
        (
            operation["both_directions"],
            operation["reverse_direction"],
            operation["end_condition"],
        ),
        "measured cut direction and termination",
    )
    depth_display = spec["depth_display"]
    if depth_display is None:
        Require(operation["depth_m"], 0, "measured through all extent")
        return
    depth = depth_display["dimension"]
    Require(depth["metres"], operation["depth_m"], "measured blind cut depth")
    dimensions = [
        item["system_value"]
        for item in feature["dimensions"]
        if item["name"] == depth["parameter_name"]
    ]
    Require(dimensions, [depth["metres"]], "measured named cut depth dimension")

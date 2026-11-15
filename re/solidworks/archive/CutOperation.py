"""Replay the packaged cut operation and check its independent measured readback."""

from DepthDisplay import display_report
from SketchRoot import Require
from convert.adapters.solidworks.resolved.cut.CutOpRead import ReadCutOp


def read_cut_operation(cursor, cut, boss):
    transfers = frozenset(index for index, name in cursor.objects.items() if name == "moAtom_c")
    parsed = ReadCutOp(cursor, cut, boss, transfers)
    end = {key: value for key, value in parsed["end_specification"].items() if key != "depth_selector_offset"}
    if end["depth_display"] is not None:
        end["depth_display"] = display_report(end["depth_display"])
    return {**parsed, "end_specification": end}


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

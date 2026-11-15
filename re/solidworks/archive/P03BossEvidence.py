"""Verify the P03 boss operation from the resolved rectangle and saved archive map."""

from math import dist, isclose

from convert.adapters.solidworks.resolved.BossEntry import ReadRectBoss
from DepthDisplay import display_report
from SketchRoot import Require

# licensed map checkpoints are bound to the two exact resolved streams they observed
CONTROLS = {
    "P03-solidworks-baseline-a.SLDPRT": {
        "resolved_sha256": "3ca4fba98bfa49213e53ee463bfd59a03e589d2ecc7253ab699bd7f21748ab72",
        "witness_sha256": "2cda0743fbe1cadeaba28a6fbfc61c526bccc6ee202b795cf629e24b1578ec72",
        "offsets": (11996, 13052, 13093, 13651, 13784, 15033, 15037),
    },
    "P03-solidworks-plane-yz.SLDPRT": {
        "resolved_sha256": "874dbab4281003a9160c81176d5a47fddcc752c4f8022e23aae29376153dad95",
        "witness_sha256": "249e1b02307ac25ac3d03a9639d39f6199b7a36df4ef8ccd6110e1efb684f4bf",
        "offsets": (12066, 13122, 13163, 13721, 13854, 15103, 15107),
    },
}


# the last resolved record must consume the exact stream after its own footer
def read_rectangle_boss(cursor, rectangle):
    file_reference = rectangle["trim"]["trim_surface"]["file_reference"]
    (transfer,) = (index for index, name in cursor.objects.items() if name == "moAtom_c")
    boss = ReadRectBoss(cursor, rectangle["profile_object"], file_reference["object_index"], transfer)
    del boss["profile_ref_offset"]
    return {
        **boss,
        "depth_display": display_report(boss["depth_display"]),
        "sketch_object": rectangle["sketch_object"],
    }


# independent map observations confirm actual operation boundaries and object ownership
def check_boss_witness(case, boss):
    control = CONTROLS.get(case["file"])
    if control is None:
        return
    Require(
        case["resolved_sha256"], control["resolved_sha256"], "licensed resolved hash"
    )
    specification = boss["end_specification"]
    display = boss["depth_display"]
    handle, dimension = display["handle"], display["dimension"]
    Require(
        (
            boss["offset"],
            specification["offset"],
            display["offset"],
            handle["offset"],
            dimension["offset"],
            boss["end"],
            boss["stream_end"],
        ),
        control["offsets"],
        "licensed boss offsets",
    )
    Require(
        (
            boss["object_index"],
            specification["object_index"],
            display["object_index"],
            handle["object_index"],
            dimension["object_index"],
            boss["from_end_object"],
            boss["next_map_index"],
        ),
        (258, 295, 296, 298, 300, 305, 306),
        "licensed boss object allocations and terminal map",
    )
    boss["native_witness_sha256"] = control["witness_sha256"]


# the prism centroid independently checks the signed displacement of the measured rectangle
def check_boss_operation(boss, rectangle, world_lines, native, tolerances):
    matches = [
        feature
        for feature in native["feature_tree"]
        if (feature["type"], feature["name"]) == ("Extrusion", boss["name"])
    ]
    Require(len(matches), 1, "independently measured owned boss")
    feature = matches[0]
    operation = feature["operation"]
    specification = boss["end_specification"]
    reversed_direction = specification["direction"] == 1
    Require(
        (
            specification["single_end"] == 0,
            reversed_direction,
            specification["conditions"][0],
        ),
        (
            operation["both_directions"],
            operation["reverse_direction"],
            operation["end_condition"],
        ),
        "measured boss direction and termination",
    )
    parameter = boss["depth_display"]["dimension"]
    depth = parameter["metres"]
    Require(depth, operation["depth_m"], "measured boss depth")
    dimensions = [
        value["system_value"]
        for value in feature["dimensions"]
        if value["name"] == parameter["parameter_name"]
    ]
    Require(dimensions, [depth], "measured named boss depth")
    basis = rectangle["support"]["transform"]["basis"] or (1, 0, 0, 0, 1, 0, 0, 0, 1)
    signed_depth = (-depth if reversed_direction else depth) * 1000
    displacement = tuple(basis[index] * signed_depth for index in (2, 5, 8))
    section = tuple(
        sum(line["start"][index] + line["end"][index] for line in world_lines) / 8
        for index in range(3)
    )
    center = tuple(
        value + movement / 2
        for value, movement in zip(section, displacement, strict=True)
    )
    Require(
        dist(center, native["center_of_mass_mm"]) <= tolerances["length_mm_absolute"],
        True,
        "measured signed boss centroid",
    )
    lengths = sorted(dist(line["start"], line["end"]) for line in world_lines)
    volume = lengths[0] * lengths[-1] * depth * 1000
    Require(native["body_count"], 1, "one measured boss body")
    Require(
        isclose(
            volume,
            native["volume_mm3"],
            rel_tol=tolerances["volume_relative"],
            abs_tol=tolerances["volume_mm3_absolute"],
        ),
        True,
        "measured boss volume",
    )
    return {
        "signed_depth_mm": signed_depth,
        "displacement_world_mm": displacement,
        "predicted_center_world_mm": center,
        "predicted_volume_mm3": volume,
    }

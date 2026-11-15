"""Join the derived CutSketch profile and its typed supporting face."""

from convert.adapters.solidworks.container.PlaneBasis import KUnitRows
from convert.adapters.solidworks.resolved.FaceIdentity import SurfaceKey
from convert.adapters.solidworks.resolved.SupportPlane import (
    ReadFaceSupport,
    RequireFaceCap,
)
from FaceEvidence import check_witness
from ProfileSupport import read_profile_body
from SketchRoot import KGeneration, Require


# every saved edge must agree with the exact boss cap selected by the cut sketch
def read_cut_support(cursor, cut, boss):
    profile = read_profile_body(cursor, cut["sketch_object"])
    prefix = ReadFaceSupport(cursor, KGeneration, Context=0)
    cap = boss["choosers"]["caps"][1]
    RequireFaceCap(prefix, cap)
    support = prefix.pop("face")
    prefix.pop("offset")
    expected = SurfaceKey(cap["primary"])
    for edge in profile["edge_references"]:
        Require(
            SurfaceKey(edge["primary"]),
            expected,
            "cut profile edge uses the reached cap",
        )
    return {
        "profile": profile,
        "support_prefix": prefix,
        "support": support,
        "end": cursor.position,
    }


# native witnesses corroborate the support byte boundaries without supplying the map
def check_cut_witness(result, witness):
    profile = result["profile"]
    prefix = result["support_prefix"]
    Require(
        (profile["kernel_packet"]["end"], profile["support_offset"], result["end"]),
        (witness["body_return"], witness["support_start"], witness["support_end"]),
        "derived cut support matches licensed byte boundaries",
    )
    Require(
        (
            profile["next_map_index"],
            prefix["ref_plane_object"],
            prefix["plane_data_start"],
        ),
        (456, 458, witness["plane_data_start"]),
        "derived cut support matches licensed local map",
    )
    if "native_atom" in witness:
        start, end = prefix["atom_span"]
        Require(
            (start, prefix["atom_arrays_offset"], end),
            witness["native_atom"],
            "derived cut atom matches licensed byte boundaries",
        )
    check_witness(result["support"], witness)


# the reopened sketch independently measures the support kind and complete transform
def check_cut_normal(result, measured_sketch):
    transform = measured_sketch["model_to_sketch_transform"]
    normal = tuple(transform[index] for index in (2, 5, 8))
    plane = result["support"]["plane"]
    Require(
        (measured_sketch["support_type"], normal),
        (2, plane["normal_world"]),
        "measured cut face support and normal",
    )
    pose = plane["transform"]
    Require(
        (*tuple(pose["basis"] or KUnitRows), *pose["translation_scale"]),
        tuple(transform[:13]),
        "measured face model to sketch transform",
    )

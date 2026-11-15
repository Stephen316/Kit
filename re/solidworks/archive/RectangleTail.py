"""Read the modern P04 rectangle profile through its principal support and trim cache."""

from convert.adapters.solidworks.container.Archive import KDefinitionKind
from convert.adapters.solidworks.resolved.ContourSurf import (
    ReadContourEdge as read_trim_edge,
    ReadTrimSurface,
)
from convert.adapters.solidworks.resolved.ContourTrim import ReadRectTrim as read_rectangle_trim
from convert.adapters.solidworks.resolved.ProfilePlane import CheckProfileRef, ReadProfileRef
from ProfileSupport import read_chain
from SketchRoot import KGeneration, Require


# the research cut reuses the file reference already materialized by the first profile
def read_trim_surface(cursor, profile, existing_file=None):
    return ReadTrimSurface(cursor, profile, existing_file)


# corner placement is valid only when its typed frame and saved datum agree
def read_principal_profile_support(cursor, planes):
    reference = ReadProfileRef(cursor, KGeneration)
    plane = next(
        (item for item in planes if item["native_feature_id"] == reference.FeatureId),
        None,
    )
    Require(plane is not None, True, "support resolves an earlier principal plane")
    plane_data = plane["plane_data"]
    CheckProfileRef(reference, plane_data["point_metres"], plane_data["normal_world"])
    return {
        "offset": reference.Offset,
        "object_index": reference.ObjectIndex,
        "unit_component": reference.UnitIndex,
        "part_object": reference.PartIndex,
        "plane_name": plane["name"],
        "plane_object": plane["object_index"],
        "native_feature_id": reference.FeatureId,
        "native_time_word": reference.TimeValue,
        "axis": reference.AxisCode,
        "transform": {
            "basis": reference.BasisValue,
            "translation_scale": reference.ShiftScale,
        },
    }


# P04 derives the expected profile contour directly from its saved sketch chain
def read_rectangle_tail(cursor, profile, planes):
    Require(cursor.read("<Ii"), (1, 1), "one modern profile chain")
    chain = read_chain(cursor, KDefinitionKind)
    support = read_principal_profile_support(cursor, planes)
    return {
        "chain": chain,
        "support": support,
        **read_rectangle_trim(cursor, profile, chain["edge_ids"], 1),
    }

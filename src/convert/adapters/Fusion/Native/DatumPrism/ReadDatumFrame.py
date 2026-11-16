# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    LinkedNodes,
    RequireFields,
    ResolveField,
)
from convert.adapters.Fusion.Native.Graph.GraphValues import ObjectFields
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)
from convert.Formats.Fusion.EntityCodec.Model.MatrixValue import MatrixValue
from convert.Geometry.Revolve.SweepVector import DotVector
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorSpace import SpaceVector

# the origin yz frame is available only for the exact measured rigid matrix
KYzMatrix = MatrixValue(
    (
        0.0,
        0.0,
        1.0,
        0.0,
        0.0,
        1.0,
        0.0,
        0.0,
        -1.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        1.0,
    )
)


# both native placements must have one reciprocal original datum and feature owner
def ReadDatumFrame(Graph: NativeGraph, Context: ExtrudeContext) -> Transform:
    Matrix = ResolveField(
        Graph, Context.SketchFeature, "rSketchPlaneMatrix", "DRMatrix"
    )
    References = LinkedNodes(Graph, Matrix, "dataRefs")
    if len(References) != 1:
        raise ValueError("Native YZ sketch requires one owned datum reference")
    Reference = References[0]
    Recipe = ResolveField(Graph, Reference, "rRecipe", "EntityRecipe")
    Datum = Graph.ResolveId(Recipe.Fields["m_entityId"])
    Origin = ResolveField(
        Graph, Context.Component, "m_rOriginWorkGeometry", "OriginWorkGeometry"
    )
    if (
        Datum.ClassName != "WorkPlane"
        or Datum not in LinkedNodes(Graph, Origin, "children")
        or Graph.Resolve(Datum.Fields["rParent"]) != Origin
        or Graph.Resolve(Origin.Fields["rParent"]) != Context.Component
        or Graph.Resolve(Context.Plane.Fields["rParent"]) != Context.Component
    ):
        raise ValueError("Native YZ recipe does not select the owned origin datum")
    RequireFields(Datum, {"originName": "YZ", "isOrigin": True, "rDcNode": None})
    Plane = ObjectFields(Datum.Fields["plane"])
    if Plane["normalReversed"] is not False:
        raise ValueError("Native YZ origin datum reverses the saved frame")
    for Owner in (Matrix, Reference):
        Update = ResolveField(Graph, Owner, "rDynamicUpdateData", "DynamicUpdateData")
        if (
            Graph.Resolve(Owner.Fields["rParentFeature"]) != Context.SketchFeature
            or Graph.Resolve(Update.Fields["rOwnerNode"]) != Owner
        ):
            raise ValueError(
                "Native YZ frame graph has a different feature or update owner"
            )
    Saved = Context.Plane.Fields["transform"]
    if (
        not isinstance(Saved, MatrixValue)
        or Saved != KYzMatrix
        or Saved != Matrix.Fields["matrix3d"]
        or Saved.Entries is None
    ):
        raise ValueError("Native YZ coordinate system and sketch matrix disagree")
    Values = Saved.Entries
    return Transform(
        origin=SpaceVector(Values[3] * 10, Values[7] * 10, Values[11] * 10),
        x_axis=SpaceVector(Values[0], Values[4], Values[8]),
        y_axis=SpaceVector(Values[1], Values[5], Values[9]),
        z_axis=SpaceVector(Values[2], Values[6], Values[10]),
    )


# convert saved world points to sketch coordinates only for geometric comparison
def LocalDatum(FrameValue: Transform, Point: KJournalVector) -> KJournalVector:
    Delta = SpaceVector(
        Point[0] - FrameValue.origin.x / 10,
        Point[1] - FrameValue.origin.y / 10,
        Point[2] - FrameValue.origin.z / 10,
    )
    return (
        DotVector(Delta, FrameValue.x_axis),
        DotVector(Delta, FrameValue.y_axis),
        DotVector(Delta, FrameValue.z_axis),
    )

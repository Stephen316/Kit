# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.adapters.freecad.EditBodyRev.BodyRevModels import GetBodyTopology
from convert.adapters.freecad.EditBodyRev.BodyRevParams import ReadSeedDepth
from convert.adapters.freecad.EditExtRing import GetEditRing
from convert.adapters.freecad.EditScale.ScaleBodyPlan import ScaleBodyPlan
from convert.formats.Fusion.Extrudes.SolidCreators import IsSavedActive
from convert.formats.Fusion.Scales.ScaleSeed import ReadScaleSeed
from convert.geometry.Extrude.Polygon.PolygonExtrude import BuildPrism
from convert.geometry.Scale.ScalePrism import BuildScalePrism
from interchange.brep.topology.BrepModel import BrepModel
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeatureBody import DesignBody
from interchange.features.FeatureDistExt import DistanceExtrude
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Selection import Selection
from interchange.geometry.models.VectorSpace import SpaceVector

# an origin scale cache receives its component translation through the root location
KScaleOrigin = SpaceVector(0, 0, 0)


# the upstream sketch and complete saved solid must agree before a live scale can replace them
def ReadScaleBody(
    Document: CadDocument,
    Feature: FeatureStep,
    Source: FeatureStep,
    Body: DesignBody,
    Pick: Selection,
    Factors: SpaceVector,
    Center: SpaceVector,
) -> tuple[ScaleBodyPlan, BrepModel]:
    Query = Pick.query
    Component = Query.get("native_component_id")
    NativeBody = Query.get("native_body_id")
    Definition = Source.definition
    if (
        Query.get("kind") != "historical_body"
        or Query.get("role") != "input"
        or type(Component) is not int
        or type(NativeBody) is not int
        or not isinstance(Definition, DistanceExtrude)
        or not IsSavedActive(Source)
        or Source.order >= Feature.order
        or Source.sketch_id is None
        or Body.id != f"fusion-derived-body-{Source.id}"
        or Body.final_feature_id != Feature.id
        or Body.provenance is None
        or Body.provenance.native_id != str(NativeBody)
        or Body.attributes.get("fusion.scale_source_feature_id") != Source.id
        or Body.attributes.get("fusion.geometry_source") != "source_profile_scale"
    ):
        raise ValueError("FreeCAD Scale body or source Extrude is unresolved")
    Sketch = next(
        (Value for Value in Document.sketches if Value.id == Source.sketch_id), None
    )
    if Sketch is None or GetEditRing(Source, Sketch) is None:
        raise ValueError("FreeCAD Scale source sketch is not an editable line profile")
    Params = tuple(
        Value for Value in Document.parameters if Value.owner_id == Source.id
    )
    Depth = ReadSeedDepth(Source, Definition, Params)
    Seed = ReadScaleSeed(Document, Source, Component)
    if Depth != Seed.Depth:
        raise ValueError("FreeCAD Scale source depth disagrees with its profile")
    World = BuildScalePrism(Body.id, Seed.Profile, Seed.Frame, Depth, Factors, Center)
    if Body.topology != GetBodyTopology(World):
        raise ValueError("FreeCAD Scale result body geometry disagrees with its source")
    SourceModel = BuildPrism(
        Body.id, Seed.Frame, Seed.Profile, min(0.0, Depth), max(0.0, Depth)
    )[0]
    ResultModel = BuildScalePrism(
        Body.id, Seed.Profile, Seed.Frame, Depth, Factors, KScaleOrigin
    )[0]
    return (
        ScaleBodyPlan(
            Body.id,
            Source.id,
            Source.sketch_id,
            Definition.AlongParameterId,
            Depth,
            SourceModel,
            ResultModel,
        ),
        World[0],
    )

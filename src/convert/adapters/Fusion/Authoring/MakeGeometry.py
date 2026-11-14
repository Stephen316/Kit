from math import radians as ToRadians, tan as Tangent

from convert.adapters.Fusion.Authoring.ProfileShape import (
    HasRectangle,
    ProfileCircle,
    ProfileLines,
)
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.geometry.Extrude.Circular.CircularExtrude import BuildCircular
from convert.geometry.Extrude.Polygon.PolygonExtrude import BuildPrism
from interchange.brep.topology.BrepModel import BrepModel
from interchange.features.FeatureBody import DesignBody
from interchange.geometry.models.Transform import Transform
from interchange.records.RecordTopology import TopologyCounts


def MakeGeometry(SpecValue: DocumentSpec) -> tuple[BrepModel, DesignBody]:
    if HasRectangle(SpecValue):
        Geometry, Volume, AreaValue, Bounds = BuildPrism(
            "body", Transform(), ProfileLines(SpecValue), 0.0, SpecValue.LengthMm
        )
    else:
        TopRadius = SpecValue.RadiusMm + SpecValue.LengthMm * Tangent(
            ToRadians(SpecValue.TaperDegrees)
        )
        Geometry, Volume, AreaValue, Bounds = BuildCircular(
            "body",
            Transform(),
            ProfileCircle(SpecValue),
            0.0,
            SpecValue.LengthMm,
            SpecValue.RadiusMm,
            TopRadius,
        )
    Counts = TopologyCounts(
        1,
        len(Geometry.shells),
        len(Geometry.faces),
        len(Geometry.edges),
        len(Geometry.vertices),
        Volume,
        AreaValue,
        Bounds,
        True,
    )
    return Geometry, DesignBody(
        "body", SpecValue.BodyName, "extrude", Counts, "material"
    )

from dataclasses import replace as ReplaceData

from interchange.brep.curves.BrepCurves import NativeCurve
from interchange.brep.curves.BrepPcurves import NativePcurve
from interchange.brep.surfaces.BrepSurfaces import NativeSurface
from interchange.brep.topology.BrepModel import BrepModel
from interchange.brep.topology.BrepTopology import BrepBody, BrepVertex
from interchange.document.models.DocumentModel import CadDocument
from interchange.geometry.models.VectorSpace import SpaceVector
from tests.interchange.fixtures.DocumentFixture import BuildDocument


# opaque geometry coverage must reach the native record guard through valid topology references
def BuildNativeBrep(RecordKind: str) -> CadDocument:
    if RecordKind == "NativeCurve":
        Geometry = BrepModel(
            curves=(NativeCurve("curve:native", "fixture.native", "unknown"),)
        )
    elif RecordKind == "NativePcurve":
        Geometry = BrepModel(
            pcurves=(NativePcurve("pcurve:native", "fixture.native", "unknown"),)
        )
    else:
        Geometry = BrepModel(
            surfaces=(NativeSurface("surface:native", "fixture.native", "unknown"),)
        )
    Geometry = ReplaceData(
        Geometry,
        vertices=(BrepVertex("vertex:1", SpaceVector(0.0, 0.0, 0.0)),),
        bodies=(
            BrepBody(
                "brep:body", (), design_body_id="body:1", vertex_ids=("vertex:1",)
            ),
        ),
    )
    return ReplaceData(BuildDocument(), brep=Geometry)

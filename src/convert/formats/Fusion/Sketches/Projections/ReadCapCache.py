from struct import unpack_from as UnpackFrom

from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.ParamProjection import ParamOrigin
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import SelectCursor
from convert.formats.Fusion.Sketches.GeometryAttrs import ReadGeomAttrs
from convert.formats.Fusion.Sketches.SketchPrimitive import ReadSketchCurve
from interchange.core.Common import FreezeMapping
from interchange.enums.EnumGeometry import GeometryKind
from interchange.geometry.models.Sketch import SketchEntity
from interchange.geometry.models.VectorPlane import PlaneVector

# the controlled cap cache is a line with typed sketch point endpoints
KCapCacheLine = "DCA267ED-D615-4934-B64F-AD805E8003E2"

# the projected cache state has a separate high bit and zero ordinary fixed or construction flags
KCapCacheState = (0x10000, 0)


# the exceptional cache state is read only for outputs named by the verified face controller
def ReadCapCache(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    Identity: int,
    SketchId: int,
    Points: dict[int, PlaneVector],
) -> SketchEntity:
    Cursor = SelectCursor(BulkData, Owners, Identity, KCapCacheLine)
    Properties = ReadGeomAttrs(Cursor)
    Start = Cursor.Offset
    Payload = Cursor.DataValue
    TagValue = Properties.get("crv_primary_id")
    if (
        len(Payload) - Start != 171
        or Properties.get("EntityGenesis") != 0
        or type(TagValue) is not int
        or Properties.get("crv_secondary_id") != 0
        or (
            UnpackFrom("<I", Payload, len(Payload) - 51)[0],
            UnpackFrom("<I", Payload, len(Payload) - 46)[0],
        )
        != KCapCacheState
    ):
        raise ValueError("Unsupported Fusion projected cap line cache state")
    Cursor.Offset = len(Payload) - 11
    if ReadNativeRef(Cursor) != SketchId:
        raise ValueError("Fusion projected cap line belongs to another sketch")
    Geometry, Extras = ReadSketchCurve(Payload, Start, Points, GeometryKind.KLine)
    return SketchEntity(
        id=f"fusion-sketch-entity-{Identity}",
        kind=GeometryKind.KLine,
        geometry=Geometry,
        provenance=ParamOrigin(Owners[Identity]),
        attributes=FreezeMapping(
            {
                **Extras,
                "fusion.entity_tag": TagValue,
                "fusion.entity_genesis": 0,
                "fusion.cap_curve_state": KCapCacheState,
            }
        ),
    )

from dataclasses import replace as Replace

from convert.formats.Fusion.ConstructionPlane.OriginDatum import ReadOriginDatum
from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.ParamProjection import ParamOrigin as RecordOrigin
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Revolves.OriginAxis import KComponentGuid
from convert.formats.Fusion.SelectionProxy import SelectCursor
from convert.formats.Fusion.Sketches.PrincipalRoute import PrincipalRoute
from interchange.core.Common import FreezeMapping
from interchange.geometry.models.SupportPlane import SupportPlane


# the sketch keeps its own basis when the datum has a different alignment in the plane
def AttachPrincipal(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    Feature: RecordSpan,
    ComponentId: int,
    PlaneValue: SupportPlane,
) -> SupportPlane:
    Origin = PlaneValue.provenance
    if Origin is None:
        return PlaneValue
    try:
        Route = PrincipalRoute(BulkData, Owners, Feature)
        PlaneId = Route[-1]
        NameValue, DatumFrame, ContainerId = ReadOriginDatum(
            BulkData, Owners, PlaneId, ComponentId
        )
        Component = SelectCursor(BulkData, Owners, ComponentId, KComponentGuid)
        Component.Offset = 66
        if (
            ReadNativeRef(Component) != ContainerId
            or NameValue not in ("XY", "YZ")
            or PlaneValue.transform.origin != DatumFrame.origin
            or PlaneValue.transform.z_axis != DatumFrame.z_axis
        ):
            return PlaneValue
    except ValueError:
        return PlaneValue
    Spans = Origin.spans + tuple(
        SpanValue
        for Identity in (Feature.ObjectId, *Route, ContainerId, ComponentId)
        for SpanValue in RecordOrigin(Owners[Identity]).spans
    )
    return Replace(
        PlaneValue,
        provenance=Replace(Origin, spans=Spans),
        attributes=FreezeMapping(
            {
                **PlaneValue.attributes,
                "fusion.native_support_resolved": True,
                "fusion.native_support_object_id": PlaneId,
                "fusion.native_support_name": NameValue,
            }
        ),
    )

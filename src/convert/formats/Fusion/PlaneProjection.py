from convert.formats.Fusion.AnglePlane.AnglePlaneSource import AttachAngleDef
from convert.formats.Fusion.HistoryPart import HistoryPart
from convert.formats.Fusion.NativePlane import KPlaneFeature, ReadNativePlane
from convert.formats.Fusion.ParamProjection import ParamOrigin as RecordOrigin
from convert.formats.Fusion.RecordSpan import RecordSpan
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.records.RecordDiagnostic import Diagnostic


# selected history limits geometry to the component being projected
def ProjectPlanes(
    BulkData: bytes, Spans: tuple[RecordSpan, ...], History: HistoryPart
) -> tuple[tuple[SupportPlane, ...], tuple[Diagnostic, ...]]:
    Owners = {
        SpanValue.ObjectId: SpanValue for SpanValue in Spans if SpanValue.IsPrimary
    }
    Planes: list[SupportPlane] = []
    Diagnostics: list[Diagnostic] = []
    for Identity in History.EntryIds:
        Feature = Owners[Identity]
        if Feature.ClassGuid != KPlaneFeature:
            continue
        try:
            PlaneValue = ReadNativePlane(BulkData, Feature, Owners)
        except ValueError as ErrorInfo:
            Diagnostics.append(
                Diagnostic(
                    code="fusion.plane.unsupported",
                    message=str(ErrorInfo),
                    provenance=RecordOrigin(Feature),
                )
            )
            continue
        try:
            Qualified = AttachAngleDef(BulkData, Owners, PlaneValue)
        except ValueError:
            Qualified = PlaneValue
        Planes.append(Qualified)
    return tuple(Planes), tuple(Diagnostics)

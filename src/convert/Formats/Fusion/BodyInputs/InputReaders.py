from convert.Formats.Fusion.BodyInputs.CombineInputs import KCombineGuid, ReadCombInputs
from convert.Formats.Fusion.BodyInputs.CutInputs import ReadCutCount, ReadCutInputs
from convert.Formats.Fusion.BodyInputs.MirrorInputs import KMirrorGuid, ReadMirrInputs
from convert.Formats.Fusion.BodyInputs.ScaleControls import KScaleGuid
from convert.Formats.Fusion.BodyInputs.ScaleInputs import ReadScaleInputs
from convert.Formats.Fusion.BodyInputs.ShellInputs import KShellGuid, ReadShellInputs
from convert.Formats.Fusion.Extrudes.ExtrudeRead import KExtrudeGuid
from convert.Formats.Fusion.RecordSpan import RecordSpan
from interchange.Enums.EnumFeatures import FeatureKind

# typed native role readers expand independently without changing history dispatch
KBodyInputReaders = {
    KCombineGuid: ("Combine", FeatureKind.KBoolean, ReadCombInputs),
    KScaleGuid: ("Scale", FeatureKind.KScale, ReadScaleInputs),
    KShellGuid: ("Shell", FeatureKind.KShell, ReadShellInputs),
    KMirrorGuid: ("Mirror", FeatureKind.KMirror, ReadMirrInputs),
    KExtrudeGuid: ("Extrude", FeatureKind.KExtrusion, ReadCutInputs),
}


# only saved cut layouts share the ordinary extrusion class with historical body selectors
def SelectInputIds(BulkData: bytes, Spans: tuple[RecordSpan, ...]) -> frozenset[int]:
    return frozenset(
        SpanValue.ObjectId
        for SpanValue in Spans
        if SpanValue.IsPrimary
        and SpanValue.ClassGuid in KBodyInputReaders
        and (
            SpanValue.ClassGuid != KExtrudeGuid
            or ReadCutCount(BulkData[SpanValue.PayloadOffset + 4 : SpanValue.EndOffset])
        )
    )

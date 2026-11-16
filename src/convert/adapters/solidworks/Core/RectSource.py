from convert.adapters.solidworks.Container.Format import PART_FORMAT_ID as KPartFormatId
from convert.adapters.solidworks.Sketch.MemberSpans import MemberSpan
from interchange.Records.RecordProvenance import Provenance, ProvenanceSpan


# source provenance must preserve its actual typed record span in the resolved stream
def RectSource(
    NativeId: str, StreamName: str, SpanValue: MemberSpan, RecordKind: str
) -> Provenance:
    return Provenance(
        KPartFormatId,
        NativeId,
        spans=(
            ProvenanceSpan(
                StreamName,
                SpanValue.Offset,
                SpanValue.EndOffset - SpanValue.Offset,
                RecordKind,
            ),
        ),
    )

from convert.formats.Fusion.Topology.AsmEdge.AsmLocation import AsmLocation
from interchange.records.RecordProvenance import ProvenanceSpan


# source member spans always address the untouched wire bytes
def AsmSourceSpan(Member: str, Origin: AsmLocation, RecordKind: str) -> ProvenanceSpan:
    return ProvenanceSpan(
        stream=Member,
        offset=Origin.StartOffset,
        length=Origin.EndOffset - Origin.StartOffset,
        record_kind=RecordKind,
    )

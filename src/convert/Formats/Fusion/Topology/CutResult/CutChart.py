from collections.abc import Callable
from hashlib import sha256 as ShaDigest

from convert.Formats.Fusion.ArchiveRead.IndexedArchive import KHistoryPrefix
from convert.Formats.Fusion.Topology.AsmEdge.AsmBodyClock import ReadBodyClock
from convert.Formats.Fusion.Topology.AsmEdge.AsmPrism import ReadAsmBody
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import ReadAsmTable
from convert.Formats.Fusion.Topology.CutResult.CutMass import CutResultStats
from convert.Formats.Fusion.Topology.CutResult.ReadResultTopo import ReadResultTopo
from interchange.Features.FeatureExtrude import ExtrudeFeature
from interchange.geometry.Models.Selection import Selection


# the verified history member digest binds final topology to the cut actor rather than the prior boss
def ReadCutChart(
    Support: Selection,
    FaceCount: int,
    Definition: ExtrudeFeature,
    LoadBlob: Callable[[str], bytes],
) -> CutResultStats:
    Member = Support.attributes.get("fusion.history_body_member")
    Digest = Support.attributes.get("fusion.history_body_sha256")
    BodyIndex = Support.attributes.get("fusion.history_body_result_ordinal")
    ClockValue = Support.attributes.get("fusion.history_body_result_clock")
    Handle = Support.attributes.get("fusion.history_body_handle")
    if (
        not isinstance(Member, str)
        or not Member.startswith(KHistoryPrefix)
        or not isinstance(Digest, str)
        or type(BodyIndex) is not int
        or type(ClockValue) is not int
        or type(Handle) is not int
    ):
        raise ValueError("Fusion Cut result lacks its mapped body revision proof")
    BlobData = LoadBlob(Member.removeprefix(KHistoryPrefix))
    if ShaDigest(BlobData).hexdigest() != Digest:
        raise ValueError(
            "Fusion Cut result history bytes differ from the verified member"
        )
    Table = ReadAsmTable(BlobData)
    if (
        ReadAsmBody(Table, Handle, frozenset((Handle,))) != BodyIndex
        or ReadBodyClock(Table, BodyIndex, Handle) != ClockValue
    ):
        raise ValueError("Fusion Cut result root or actor clock disagrees")
    return ReadResultTopo(Table, BodyIndex, FaceCount, Definition)

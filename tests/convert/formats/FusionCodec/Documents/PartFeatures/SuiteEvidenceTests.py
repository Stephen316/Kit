from hashlib import sha256 as HashBytes
from json import loads as LoadJson
from typing import cast as CastValue

from pytest import mark as MarkTests

from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from tests.convert.formats.FusionCodec.Documents.PartFeatures.BulletinRefs import (
    IsIdentityRef,
)
from tests.convert.formats.FusionCodec.Documents.PartFeatures.PartCases import (
    KOracleRoot,
)

KAuthored = KOracleRoot / "Authored"
KSuites = (
    "NativeAcceptance.json",
    "NativeAcceptanceExtrudes.json",
    "NativeAcceptanceHoles.json",
    "NativeAcceptancePatterns.json",
    "NativeAcceptanceMulti.json",
    "NativeAcceptanceEdges.json",
    "NativeAcceptanceConstruction.json",
    "NativeAcceptanceRevolves.json",
    "NativeAcceptanceCountersinks.json",
    "NativeAcceptanceShells.json",
    "NativeAcceptanceMoves.json",
    "NativeAcceptanceOffsets.json",
    "NativeAcceptanceDrafts.json",
    "NativeAcceptanceBodies.json",
    "NativeAcceptanceLofts.json",
    "NativeAcceptanceSweeps.json",
    "NativeAcceptancePastes.json",
    "NativeAcceptanceRounds.json",
)


def ReadReport(NameValue: str) -> dict[str, object]:
    return CastValue(dict[str, object], LoadJson((KAuthored / NameValue).read_text()))


@MarkTests.parametrize("SuiteName", KSuites)
def TestSuiteReport(SuiteName: str) -> None:
    Manifest = CastValue(dict[str, dict[str, object]], ReadReport("Manifest.json"))
    Report = ReadReport(SuiteName)
    assert Report["status"] == "accepted"
    assert Report["documents_before"] == Report["documents_after"] == 0
    Cases = CastValue(list[dict[str, object]], Report["cases"])
    assert Cases
    for Entry in Cases:
        NameValue = CastValue(str, Entry["name"])
        Payload = (KAuthored / CastValue(str, Entry["file"])).read_bytes()
        Digest = HashBytes(Payload).hexdigest()
        assert Digest == Manifest[NameValue]["sha256"] == Entry["sha256"]
        assert Entry["status"] == "accepted"
        History = ReadDocument(Payload).Bodies[0].History
        assert isinstance(History, JournalModel)
        assert IsIdentityRef(History)

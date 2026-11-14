from hashlib import sha256 as HashBytes
from json import loads as LoadJson
from typing import cast as CastValue

from pytest import mark as MarkTests

from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from tests.convert.formats.FusionCodec.Documents.PartFeatures.PartCases import (
    KFamilyClasses,
    KOracleRoot,
    KPartCases,
)
from tests.convert.formats.FusionCodec.Documents.PartFeatures.PartRecords import (
    PartRecords,
)

KAuthored = KOracleRoot / "Authored"


def ReadReport(NameValue: str) -> dict[str, object]:
    return CastValue(dict[str, object], LoadJson((KAuthored / NameValue).read_text()))


@MarkTests.parametrize("NameValue", tuple(KPartCases))
def TestEvidence(NameValue: str) -> None:
    Manifest = CastValue(dict[str, dict[str, object]], ReadReport("Manifest.json"))
    Report = ReadReport("NativeAcceptance.json")
    assert Report["status"] == "accepted"
    assert Report["documents_after"] == 0
    Cases = CastValue(list[dict[str, object]], Report["cases"])
    Matched = next(Entry for Entry in Cases if Entry["name"] == NameValue)
    Payload = (KAuthored / (NameValue + ".f3d")).read_bytes()
    Digest = HashBytes(Payload).hexdigest()
    assert Digest == Manifest[NameValue]["sha256"] == Matched["sha256"]
    assert Matched["status"] == "accepted"
    Model = ReadDocument(Payload)
    Found = sum(
        len(PartRecords(Model, ClassName)) for ClassName in set(KFamilyClasses.values())
    )
    assert Found == len(KPartCases[NameValue])

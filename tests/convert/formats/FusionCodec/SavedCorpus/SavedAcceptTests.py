from hashlib import sha256 as HashBytes
from json import loads as LoadJson
from pathlib import Path as FilePath
from sys import version_info as PythonVersion
from typing import cast as CastValue

from pytest import mark as TestMarks

from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument

KRoot = FilePath(__file__).resolve().parents[5]

KFolder = KRoot / "re" / "Fusion" / "LocalOracle" / "ReaderCoverage"

KRequiresCodec = TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)


def LoadCases(FileName: str) -> list[dict[str, object]]:
    Report = CastValue(
        dict[str, object], LoadJson((KFolder / FileName).read_text("utf-8"))
    )
    return CastValue(list[dict[str, object]], Report["cases"])


def LoadReport() -> dict[str, object]:
    return CastValue(
        dict[str, object],
        LoadJson((KFolder / "NativeAcceptance.json").read_text("utf-8")),
    )


def ReadText(Entry: dict[str, object], FieldName: str) -> str:
    Value = Entry[FieldName]
    assert isinstance(Value, str)
    return Value


@KRequiresCodec
def TestPrepared() -> None:
    Cases = LoadCases("Preparation.json")
    assert len(Cases) == 26
    for Entry in Cases:
        Source = (KRoot / ReadText(Entry, "source")).read_bytes()
        Output = (KRoot / ReadText(Entry, "output")).read_bytes()
        assert HashBytes(Source).hexdigest() == ReadText(Entry, "source_sha256")
        assert HashBytes(Output).hexdigest() == ReadText(Entry, "output_sha256")
        Model = ReadDocument(Source)
        assert EmitParsed(Model) == Output
        assert ReadDocument(Output) == Model


def TestNativeRun() -> None:
    Report = LoadReport()
    assert Report["status"] == "accepted"
    assert Report["documents_after"] == 0
    assert Report["fusion_version"] == "2706.1.17"
    Prepared = {
        ReadText(Entry, "label"): ReadText(Entry, "output_sha256")
        for Entry in LoadCases("Preparation.json")
    }
    Cases = CastValue(list[dict[str, object]], Report["cases"])
    assert {ReadText(Entry, "name") for Entry in Cases} == set(Prepared)
    for Entry in Cases:
        assert Entry["status"] == "accepted"
        assert ReadText(Entry, "output_sha256") == Prepared[ReadText(Entry, "name")]
        Variants = CastValue(list[dict[str, object]], Entry["variants"])
        assert [ReadText(Variant, "name") for Variant in Variants] == [
            "Control",
            "Reemitted",
        ]
        assert ReadText(Variants[1], "source_sha256") == ReadText(
            Entry, "output_sha256"
        )
        assert all(Variant["status"] == "accepted" for Variant in Variants)


@KRequiresCodec
def TestSavedReads() -> None:
    for Entry in CastValue(list[dict[str, object]], LoadReport()["cases"]):
        for Variant in CastValue(list[dict[str, object]], Entry["variants"]):
            Payload = (KRoot / ReadText(Variant, "saved")).read_bytes()
            assert HashBytes(Payload).hexdigest() == ReadText(Variant, "saved_sha256")
            Model = ReadDocument(Payload)
            assert ReadDocument(EmitParsed(Model)) == Model

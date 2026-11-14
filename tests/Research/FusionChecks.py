import hashlib as Hashlib
import json as JsonCodec
from collections import Counter
from pathlib import Path as FilePath

from interchange.document.models.DocumentModel import CadDocument
from tests.Research.FusionClient import KControlAsset


def VerifyControl(TargetPath: FilePath, Entry: dict[str, str]) -> None:
    AssetPath = TargetPath / Entry["directory"]
    DocBytes = (AssetPath / "document.json").read_bytes()
    Receipt = JsonCodec.loads((AssetPath / "receipt.json").read_text())
    Document = CadDocument.from_json(DocBytes.decode("utf-8"))
    Document.assert_valid()
    assert tuple(Value.name for Value in Document.parameters) == ("d1", "d2")
    assert len(Document.feature_timeline) == 2
    assert not Document.brep_payloads
    assert not Document.diagnostics
    assert Receipt["neutral_sha256"] == Hashlib.sha256(DocBytes).hexdigest()
    assert Receipt["neutral_sha256"] == Entry["neutral_sha256"]
    assert Receipt["fingerprint"] == Entry["fingerprint"]
    assert Receipt["source"]["path"] == KControlAsset
    assert Document.source.sha256 == Receipt["source"]["sha256"]
    assert Receipt["options"]["allow_partial"] is False
    assert Receipt["strict_rejection"] is None
    assert Receipt["validation"] == "model_and_reconstruction_passed"
    assert Receipt["semantic_qualification"] == "unverified"
    assert Receipt["native_acceptance"] == "not_established"
    assert Receipt["portable_complete"] is False
    assert Receipt["unresolved"]
    assert all(Record["status"] != "qualified" for Record in Receipt["records"])


def VerifyDecoded(
    TargetPath: FilePath,
    Entry: dict[str, str],
    AssetMap: dict[str, dict[str, str | int]],
) -> None:
    AssetPath = TargetPath / Entry["directory"]
    DocBytes = (AssetPath / "document.json").read_bytes()
    Receipt = JsonCodec.loads((AssetPath / "receipt.json").read_text())
    assert Receipt["source"] == AssetMap[Entry["path"]]
    assert Receipt["neutral_sha256"] == Hashlib.sha256(DocBytes).hexdigest()
    assert Receipt["reader_mode"] == Entry["reader_mode"]
    assert Receipt["semantic_qualification"] == "unverified"
    assert Receipt["portable_complete"] is False
    assert Receipt["unresolved"]
    if Entry["reader_mode"] == "partial":
        assert Receipt["strict_rejection"]


def VerifyChunk(
    TargetPath: FilePath, AssetMap: dict[str, dict[str, str | int]]
) -> list[dict[str, str]]:
    Summary = JsonCodec.loads((TargetPath / "summary.json").read_text())
    assert Summary["allow_partial"] is True
    Entries: list[dict[str, str]] = Summary["assets"]
    for Entry in Entries:
        if Entry["outcome"] == "decoded":
            VerifyDecoded(TargetPath, Entry, AssetMap)
        else:
            assert "directory" not in Entry
            assert Entry["reason"]
    return Entries


def ReportCensus(Entries: list[dict[str, str]]) -> None:
    Outcomes = Counter(Entry.get("reader_mode", Entry["outcome"]) for Entry in Entries)
    Reasons = Counter(
        Entry["reason"][:120] for Entry in Entries if Entry["outcome"] != "decoded"
    )
    print(
        JsonCodec.dumps(
            {
                "fusion_reader_corpus": {
                    "assets": len(Entries),
                    "outcomes": dict(sorted(Outcomes.items())),
                    "reasons": Reasons.most_common(25),
                }
            },
            sort_keys=True,
        )
    )

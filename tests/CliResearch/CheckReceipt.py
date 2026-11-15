from hashlib import sha256 as HashContent
from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess

from tests.CliResearch.ResearchRoot import ResearchRoot


# research artifacts must identify their exact sdk sources without implying portable completeness
def CheckReceipt(ArtifactPath: FilePath) -> None:
    RootPath = ResearchRoot()
    Receipt = LoadJson((ArtifactPath / "receipt.json").read_bytes())
    Revision = RunProcess(
        ("git", "-C", str(RootPath), "rev-parse", "HEAD"),
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    ).stdout.strip()
    assert Receipt["sdk_revision"] == Revision
    Sources = {
        str(Source.relative_to(RootPath)): HashContent(Source.read_bytes()).hexdigest()
        for Source in sorted((RootPath / "src").rglob("*.py"))
    }
    assert (
        Receipt["sdk_sources_sha256"]
        == HashContent(
            DumpJson(Sources, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
    )
    Document = (ArtifactPath / "document.json").read_bytes()
    assert Receipt["neutral_sha256"] == HashContent(Document).hexdigest()
    assert Receipt["portable_complete"] is False
    assert LoadJson(Document)["metadata"]["kit.research_read_status"] == "unqualified"

import hashlib as Hashlib
import json as JsonCodec
import subprocess as Subprocess
import sys as System
import tempfile as TempFiles
from pathlib import Path as FilePath

from interchange.document.models.DocumentModel import CadDocument


def CheckReadFlow() -> None:
    RootPath = FilePath(__file__).resolve().parents[2]
    with TempFiles.TemporaryDirectory() as TempPath:
        TargetPath = FilePath(TempPath) / "Decoded"
        Command = [
            System.executable,
            str(RootPath / "re/automation/SolidworksReader.py"),
            "--asset",
            "re/solidworks/examples/.SLDPRT/example.SLDPRT",
            "--output",
            str(TargetPath),
        ]
        ResultInfo = Subprocess.run(
            Command, capture_output=True, text=True, timeout=120, check=False
        )
        assert ResultInfo.returncode == 0, ResultInfo.stderr
        Summary = JsonCodec.loads(ResultInfo.stdout)
        Receipt = JsonCodec.loads((TargetPath / "receipt.json").read_text())
        DocBytes = (TargetPath / "document.json").read_bytes()
        Document = CadDocument.from_json(DocBytes.decode("utf-8"))
        Document.assert_valid()
        assert Document.feature_timeline
        assert Document.sketches
        assert Receipt["neutral_sha256"] == Hashlib.sha256(DocBytes).hexdigest()
        assert Document.source.sha256 == Receipt["source"]["sha256"]
        assert Summary["fingerprint"] == Receipt["fingerprint"]
        assert Receipt["validation"] == "model_and_reconstruction_passed"
        assert Receipt["portable_complete"] is False
        assert Receipt["native_acceptance"] == "not_established"
        assert Receipt["byte_accounting"] == "unavailable"
        assert Receipt["fields"]
        assert any(
            Entry["reason"] == "retained_bytes_are_not_portable_semantics"
            for Entry in Receipt["unresolved"]
        )
        assert all(Entry["status"] != "qualified" for Entry in Receipt["records"])
        PriorData = (TargetPath / "receipt.json").read_bytes()
        ResultInfo = Subprocess.run(
            Command, capture_output=True, text=True, timeout=120, check=False
        )
        assert ResultInfo.returncode == 1
        assert (TargetPath / "receipt.json").read_bytes() == PriorData

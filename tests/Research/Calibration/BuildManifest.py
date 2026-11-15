import hashlib as HashCodec
import json as JsonCodec
from pathlib import Path as FilePath

from convert import write_document as WriteDocument
from tests.convert.api.Fusion.AdapterCases import AdapterCase


def BuildManifest(RootPath: FilePath, JobCount: int = 8) -> FilePath:
    InputPath = RootPath / "Input.f3d"
    _ = WriteDocument(
        AdapterCase("rectangle"),
        InputPath,
        destination_format="f3d",
        allow_carrier=False,
    )
    Content = InputPath.read_bytes()
    Manifest = {
        "calibration_version": 1,
        "kind": "decode.fusion",
        "pool": "offline",
        "runner": {"threads": 1, "initial_peak_memory_mib": 64, "max_memory_mib": 1024},
        "bindings": {
            "source:calibration": {
                "path": InputPath.name,
                "sha256": HashCodec.sha256(Content).hexdigest(),
                "size_bytes": len(Content),
            }
        },
        "resources": {"offline:slot": {"capacity": 1, "available": True}},
        "reserved_cpus": 1,
        "reserved_memory_mib": 64,
        "max_seconds": 30,
        "jobs": [
            {
                "id": f"offline:sample{Index}",
                "kind": "decode.fusion",
                "inputs": {"source": "source:calibration"},
                "rule_version": "decode@1",
                "tool_version": "fixture@1",
                "resources": ["offline:slot"],
                "options": {"allow_partial": False},
                "max_attempts": 1,
                "lease_seconds": 3,
                "timeout_seconds": 30,
            }
            for Index in range(JobCount)
        ],
    }
    ManifestPath = RootPath / "CalibrationManifest.json"
    _ = ManifestPath.write_text(JsonCodec.dumps(Manifest), encoding="utf-8")
    return ManifestPath

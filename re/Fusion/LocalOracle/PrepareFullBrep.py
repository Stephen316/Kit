import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

root = Path(__file__).resolve().parent
source = root / "Features/kit_cacheless_19mm.f3d"
output = root / "Features/kit_full_brep_19mm.f3d"
snapshot = root.parent / "Reconstruction/SnapshotAuthoring/IndependentNineteen.smb"
with ZipFile(source) as archive:
    names = [name for name in archive.namelist() if name.endswith(".smb")]
    if len(names) != 1:
        raise RuntimeError("Expected one snapshot geometry member")
    with ZipFile(output, "w") as target:
        for entry in archive.infolist():
            target.writestr(entry, snapshot.read_bytes() if entry.filename == names[0] else archive.read(entry))
report = {"source": source.name, "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "output": output.name, "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest(), "independent_snapshot_sha256": hashlib.sha256(snapshot.read_bytes()).hexdigest(), "replaced_member": names[0], "scope": "Both BRep members independently authored from dimensions and explicit identities; all Design records reconstructed from typed fields; OGS omitted; remaining source envelope retained, not independent full document generation"}
(root / "Features/FullBrepRewrite.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))

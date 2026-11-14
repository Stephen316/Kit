import hashlib
import json
import sys
from dataclasses import asdict
from pathlib import Path
from zipfile import ZipFile

root = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(root / "src"))
from convert.formats.Fusion.BrepCodec.Frustum.ReadFrustumHist import ReadFrustumHist
from convert.formats.Fusion.BrepCodec.Frustum.EmitFrustumHist import EmitFrustumHist

folder = Path(__file__).resolve().parent
source = root / "re/Fusion/Study/timeline-5867579925b5/rolled_back.f3d"
target = folder / "RolledHistoryReemitted.f3d"
with ZipFile(source) as archive:
    names = [name for name in archive.namelist() if name.endswith(".smbh")]
    if len(names) != 1:
        raise ValueError("Expected one native history")
    original = archive.read(names[0])
    model = ReadFrustumHist(original)
    emitted = EmitFrustumHist(model.Model, model.Identity, model.TagSet, model.History, model.Stamp, model.Frame)
    with ZipFile(target, "w") as output:
        for entry in archive.infolist():
            output.writestr(entry, emitted if entry.filename == names[0] else archive.read(entry))
report = {"scope": "Native acceptance artifact preparation through the complete typed frustum history codec; source-specific other archive members preserved; no local tests", "source": str(source), "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "output": str(target), "output_sha256": hashlib.sha256(target.read_bytes()).hexdigest(), "source_history_sha256": hashlib.sha256(original).hexdigest(), "history_sha256": hashlib.sha256(emitted).hexdigest(), "history_bytes": len(emitted), "model": asdict(model.Model), "history": asdict(model.History)}
(folder / "Preparation.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))

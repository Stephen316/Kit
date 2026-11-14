import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

root = Path(__file__).resolve().parent / "Features"
source = root / "kit_cached_19mm.f3d"
output = root / "kit_cacheless_19mm.f3d"
removed = []
with ZipFile(source) as archive, ZipFile(output, "w") as target:
    for entry in archive.infolist():
        if "/OGS.BlobFolder/" in entry.filename:
            removed.append(entry.filename)
        else:
            target.writestr(entry, archive.read(entry))
report = {"source": source.name, "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "output": output.name, "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest(), "removed": removed, "scope": "Controlled omission of OGS graphics caches from same-source typed Design and independently authored solved BRep archive; no claim that all cache families are optional"}
(root / "NoGraphicsRewrite.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))

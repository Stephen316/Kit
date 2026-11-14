import hashlib
import json
import runpy
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
FOLDER = Path(__file__).resolve().parent
SOURCE = ROOT / "re/Fusion/Study/extents-f0f33a9a605f/taper.f3d"
READER = runpy.run_path(str(ROOT / "re/Fusion/Reconstruction/BrepTokens.py"))["read_stream"]


def main():
    ground_path = SOURCE.parent / "ground_truth.json"
    ground = json.loads(ground_path.read_text())
    sample = next(row for row in ground["samples"] if row["file"] == "taper.f3d")
    with zipfile.ZipFile(SOURCE) as archive:
        member = next(name for name in archive.namelist() if name.endswith(".smbh"))
        data = archive.read(member)
    parsed = READER(data)
    selected = []
    for row in parsed["records"]:
        if row["boundary_marker"]:
            break
        if row["name"] in ("cone-surface", "ellipse-curve", "plane-surface", "point", "edge", "vertex"):
            selected.append(row)
    report = {
        "scope": "Read-only source-data inspection; no runtime calls or product execution. The earlier static library inspection was removed.",
        "source": str(SOURCE.relative_to(ROOT)),
        "sourceSha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "groundTruthSha256": hashlib.sha256(ground_path.read_bytes()).hexdigest(),
        "groundTruth": sample,
        "member": member,
        "memberSha256": hashlib.sha256(data).hexdigest(),
        "header": parsed["header"],
        "records": selected,
        "canonicalEquation": "p(u,v)=base+(rb+u*scale*sinAngle)*(cos(v),sin(v),0)+(0,0,u*scale*cosAngle); circular forward cone, cosine positive",
        "authoredParameters": {
            "deltaRadius": "rt-rb", "slant": "hypot(height,rt-rb)",
            "sinAngle": "(rt-rb)/slant", "cosAngle": "height/slant", "scale": "rb",
            "upperU": "height/(rb*cosAngle)", "radialLaw": "r(z)=rb+z*sinAngle/cosAngle",
        },
        "upstream": {
            "url": "https://github.com/jmplonka/InventorLoader/blob/master/Acis.py",
            "class": "SurfaceCone", "lines": [2767, 2828],
            "corroboration": "Parser independently names sine/cosine and reads the following field as length; its apex reconstruction agrees with center-axis*radius*cosine/sine",
            "codeCopied": False,
        },
        "limits": [
            "Canonical circular forward cone only; reversed sense, negative cosine, ellipse ratio not one and bounded UV ranges are not implemented",
            "Topology construction is independent; native taper happens to serialize the upper ellipse with axis -Z, while the authored loops use +Z with complementary coedge senses",
            "No apex: both authored cap radii are strictly positive",
        ],
    }
    (FOLDER / "ConeEvidence.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in ("source", "sourceSha256", "memberSha256")}))


if __name__ == "__main__":
    main()

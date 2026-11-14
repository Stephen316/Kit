"""Check that the unified spline journal model still carries every Form archive.

Usage: python3.14 -I VerifyForms.py
Reads the Form archive list used by the spline tests, round-trips each archive
through ReadDocument/EmitParsed, round-trips each .smb/.smbh member through the
journal codecs, compares ListPrograms with the archive's .tsm program, and
checks that forward and family-mismatched subtype references are rejected.
Writes VerifyForms.json next to this script.
"""
import dataclasses
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from convert.formats.Fusion.BrepCodec.Journal.Complex.Subtypes.EntitySubtree import EntitySubtree, SwapSubtree  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Complex.Subtypes.WalkSubtypes import MapSubtypes, WalkSubtypes  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.EmitJournal import EmitJournal  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.ReadJournal import ReadJournal  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.EmitGeometry import EmitGeometry  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.ReadGeometry import ReadGeometry  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Spline.ListPrograms import ListPrograms  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Spline.ListSubtypes import ListSubtypes  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Spline.PcurveNode import PcurveNode  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Spline.SplineNode import SplineNode  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Spline.SubtypeRef import SubtypeRef  # noqa: E402
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed  # noqa: E402
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument  # noqa: E402
from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline  # noqa: E402
from tests.convert.formats.FusionCodec.Documents.Form.FormArchives import KFormArchives  # noqa: E402


def members(data):
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        return {info.filename: archive.read(info.filename) for info in archive.infolist() if not info.filename.endswith("/")}


def fault(geometry, target):
    for index, value in enumerate(geometry.Entities):
        if not isinstance(value, PcurveNode):
            continue
        refs = [found for found in WalkSubtypes(EntitySubtree(value)) if isinstance(found, SubtypeRef)]
        if not refs:
            continue
        mapping = {found.Index: target for found in refs}
        entities = list(geometry.Entities)
        entities[index] = SwapSubtree(value, MapSubtypes(EntitySubtree(value), mapping))
        try:
            EmitGeometry(dataclasses.replace(geometry, Entities=tuple(entities)))
        except ValueError as error:
            return "rejected: " + str(error)
        return "accepted"
    return "no pcurve reference"


def main():
    rows = []
    spline_members = 0
    for relative, digest in KFormArchives:
        data = (ROOT / relative).read_bytes()
        assert hashlib.sha256(data).hexdigest() == digest
        emitted = EmitParsed(ReadDocument(data))
        before, after = members(data), members(emitted)
        changed = sorted(name for name in before if after.get(name) != before[name] and not name.endswith(".protein"))
        row = {"archive": relative, "document_changed_members": changed, "members": []}
        program = next(payload for name, payload in before.items() if name.endswith(".tsm"))
        for name, payload in before.items():
            if not name.endswith((".smb", ".smbh")):
                continue
            model = ReadGeometry(payload) if name.endswith(".smb") else ReadJournal(payload)
            out = EmitGeometry(model) if name.endswith(".smb") else EmitJournal(model)
            entry = {
                "member": name.rsplit("/", 1)[-1],
                "exact": out == payload,
                "spline": any(isinstance(value, SplineNode) for value in model.Entities),
                "programs_match": ListPrograms(model.Entities) == (ReadTspline(program),),
            }
            if name.endswith(".smb"):
                kinds = [kind for value in model.Entities for kind, index in ListSubtypes(value) if index is None]
                entry["forward_fault"] = fault(model, 4096)
                if "exact_int_cur" in kinds:
                    entry["kind_fault"] = fault(model, kinds.index("exact_int_cur"))
            spline_members += 1
            row["members"].append(entry)
        rows.append(row)
    report = {
        "archives": len(rows),
        "spline_members": spline_members,
        "all_exact": all(entry["exact"] for row in rows for entry in row["members"]),
        "all_programs_match": all(entry["programs_match"] for row in rows for entry in row["members"]),
        "all_spline": all(entry["spline"] for row in rows for entry in row["members"]),
        "documents_unchanged": all(not row["document_changed_members"] for row in rows),
        "faults_rejected": all(
            entry.get(key, "rejected").startswith("rejected")
            for row in rows for entry in row["members"] for key in ("forward_fault", "kind_fault")
        ),
        "rows": rows,
    }
    (BASE / "VerifyForms.json").write_text(json.dumps(report, indent=1) + "\n")
    print(json.dumps({key: value for key, value in report.items() if key != "rows"}, indent=1))


main()

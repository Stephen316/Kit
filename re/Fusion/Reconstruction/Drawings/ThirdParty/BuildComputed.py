import hashlib
import io
import json
import os
import sys
import zipfile
from dataclasses import replace
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / "Authoring"))
sys.path.insert(0, str(HERE.parents[4] / "src"))

import BuildVariants

class common:
    @staticmethod
    def safe(getter, default=None):
        try:
            return getter()
        except Exception:
            return default

from BuildPruned import emit_fresh

from convert.Formats.Fusion.DrawingCodec.Dwg.Author.ShellParts import AuthorAppInfo
from convert.Formats.Fusion.DrawingCodec.Dwg.Header.HeaderFrame import KHeaderName
from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgAppEntry import DwgAppEntry
from convert.Formats.Fusion.DrawingCodec.Dwg.ReadDwgFile import ReadDwgFile
from convert.Formats.Fusion.DrawingCodec.Dwg.ReadDwgInventory import ReadInventory

OLD = Path(os.environ.get("KIT_DRAWING_SRC", "/private/var/folders/b0/tf903gr929v3hkcly_v3dl800000gn/T/KitFusionDrawings/Variants"))
OUT = Path(os.environ.get("KIT_DRAWING_OUT", str(HERE / "Out"))) / "Variants"
COMMENT = "This file was last saved by Kit."
SOURCE_LABEL = os.environ.get("KIT_DRAWING_SOURCE", "K1SheetOnly")
LABEL = os.environ.get("KIT_COMPUTED_LABEL", "C18ComputedTail")


def source_parts(label):
    path = OLD / f"{label}.f3z"
    with zipfile.ZipFile(io.BytesIO(path.read_bytes())) as archive:
        names = archive.namelist()
        drawing_name = next(name for name in names if name.endswith(".f2d"))
        design_name = next(name for name in names if name.endswith(".f3d"))
        return archive.read(design_name), archive.read(drawing_name)


def third_party_info(comment=COMMENT):
    authored = AuthorAppInfo()
    return replace(
        authored,
        AppEntries=authored.AppEntries + (DwgAppEntry(bytes(16), comment),),
    )


def header_bytes(content):
    inventory = ReadInventory(content)
    for section in inventory.Sections:
        if section.SectionInfo.SectionName == KHeaderName:
            return section.DataValue
    return b""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    BuildVariants.OUT = OUT
    source, drawing = source_parts(SOURCE_LABEL)
    base = ReadDwgFile(BuildVariants.database(drawing))
    source_header = header_bytes(BuildVariants.database(drawing))
    if os.environ.get("KIT_COMPUTED_RAW") == "1":
        data = BuildVariants.database(drawing)
    else:
        dwg = replace(base, AppInfo=third_party_info())
        data = emit_fresh(dwg)
    again = base if os.environ.get("KIT_COMPUTED_RAW") == "1" else ReadDwgFile(data)
    emitted_header = header_bytes(data)
    row = {
        "label": LABEL,
        "source": SOURCE_LABEL,
        "file": f"{LABEL}.f3z",
        "dwg_bytes": len(data),
        "dwg_sha256": hashlib.sha256(data).hexdigest(),
        "dwg_version": data[:6].decode("latin-1"),
        "source_dwg_sha256": hashlib.sha256(
            BuildVariants.database(drawing)
        ).hexdigest(),
        "comment": again.AppInfo.AppEntries[-1].TextValue,
        "source_header_sha256": hashlib.sha256(source_header).hexdigest(),
        "emitted_header_sha256": hashlib.sha256(emitted_header).hexdigest(),
        "header_matches_source": emitted_header == source_header,
        "tail_width": common.safe(lambda: dict(again.SectionVars)[KHeaderName].RecordFields[0].FieldValue),
    }
    bundle = BuildVariants.opaque_bundle(
        BuildVariants.without_database(drawing, data), source, LABEL
    )
    path = OUT / f"{LABEL}.f3z"
    path.write_bytes(bundle)
    row["bytes"] = len(bundle)
    row["sha256"] = hashlib.sha256(bundle).hexdigest()
    (OUT / f"{LABEL}.dwg").write_bytes(data)
    (OUT / "PlanComputed.json").write_text(
        json.dumps({"variants": [row]}, indent=1) + "\n"
    )
    print(json.dumps(row, indent=1))


if __name__ == "__main__":
    main()

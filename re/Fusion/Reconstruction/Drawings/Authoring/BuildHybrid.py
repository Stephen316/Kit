"""Build hybrid drawings that locate the part of an authored drawing that Fusion rejects.

Fusion showed "Drawing file is not valid" for L5SheetDimension, whose F2D and DWG are both authored by Kit.
Each hybrid swaps one of the two for a member that Fusion has opened:

  N1AuthoredDwg   the A1 control F2D with the authored L5 DWG
  N2AuthoredF2d   a Kit-built F2D with the H1NoAcm DWG, which Fusion opened with all views and the dimension

Usage: BuildHybrid.py --control <A1 f2d> --source <design f3d> --authored <L5 dwg> --opened <H1NoAcm f3z>
"""

import argparse
import hashlib
import json
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[4] / 'src'))

import BuildAuthored  # noqa: E402
import BuildVariants  # noqa: E402

from convert.formats.Fusion.DrawingCodec.Author.BuildBundle import BuildBundle  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Author.BuildDrawing import BuildDrawing  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Author.MakeIdentity import MakeIdentity  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Author.Model.DrawingSpec import DrawingSpec  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Author.Model.SheetSpec import SheetSpec  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Bundle.EmitDrawBundle import EmitDrawBundle  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Bundle.ReadDrawBundle import ReadDrawBundle  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.ReadDwgFile import ReadDwgFile  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Model.DrawingDatabase import DrawingDatabase  # noqa: E402
from convert.formats.Fusion.DrawingCodec.ReadDrawing import ReadDrawing  # noqa: E402


def sheet_layout(dwg):
    """Return the handle and name of the one paper-space layout."""
    found = []
    for obj in ReadDwgFile(dwg).DwgObjects:
        if obj.ClassKind == 'LAYOUT':
            name = next(item.FieldValue for item in obj.ClassData.RecordFields if item.FieldName == 'LayoutName')
            if name != 'Model':
                found.append((obj.ObjectHandle, name))
    if len(found) != 1:
        raise ValueError(f'expected one sheet layout, found {len(found)}')
    return found[0]


def record(label, bundle, dwg):
    path = BuildVariants.OUT / f'{label}.f3z'
    path.write_bytes(bundle)
    return {'label': label, 'file': path.name, 'bytes': len(bundle), 'sha256': hashlib.sha256(bundle).hexdigest(),
            'dwg_bytes': len(dwg), 'dwg_sha256': hashlib.sha256(dwg).hexdigest()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--control', required=True)
    parser.add_argument('--source', required=True)
    parser.add_argument('--authored', required=True)
    parser.add_argument('--opened', required=True)
    args = parser.parse_args()
    control_bytes = Path(args.control).read_bytes()
    design = Path(args.source).read_bytes()
    authored = Path(args.authored).read_bytes()
    rows = []
    hybrid = BuildVariants.without_database(control_bytes, authored)
    rows.append(record('N1AuthoredDwg', BuildVariants.opaque_bundle(hybrid, design, 'N1AuthoredDwg'), authored))
    opened = ReadDrawBundle(Path(args.opened).read_bytes(), BuildVariants.inflate).Drawing.Database.Content
    handle, name = sheet_layout(opened)
    control = ReadDrawing(control_bytes, BuildVariants.inflate)
    spec = DrawingSpec('N2AuthoredF2d', BuildAuthored.design_target(control), SheetSpec(name), MakeIdentity(), handle)
    drawing = BuildDrawing(spec, DrawingDatabase('ExtFile.' + str(uuid.uuid4()) + '.dwg', opened))
    bundle = EmitDrawBundle(BuildBundle(spec, drawing, design), BuildVariants.compress)
    rows.append(record('N2AuthoredF2d', bundle, opened))
    (BuildVariants.OUT / 'Plan6.json').write_text(json.dumps({'variants': rows}, indent=1) + '\n')
    print(json.dumps(rows, indent=1))


if __name__ == '__main__':
    main()

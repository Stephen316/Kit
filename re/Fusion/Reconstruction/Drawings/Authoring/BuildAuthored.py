"""Build source-free authored drawings with Kit's DWG and F2D authors for native acceptance.

Every authored bundle is built from typed inputs only. The DWG comes from AuthorDwg, the drawing
members from BuildDrawing and the bundle from BuildBundle, all with fresh identities. No byte of a
captured DWG or drawing is copied.

The referenced design is the acceptance source design. Its typed description comes from two places:

* DesignTarget values (asset, snapshot, component, body and entity ids) are read from the A1
  capture's link to that same design, because they describe the design, not the drawing;
* ViewSource values come from the design itself: body id 306 (the "0_306" entity of the source),
  the body geometry revision GUID from the ACT segment, and the 40 x 20 x 10 mm body box.

Labels:
  K1SheetOnly     sheet, border and title block, no views
  K2BaseView      plus one base view from the front
  K3ThreeViews    base view with projected right and top views
  K4StaleViews    K3 with a zero geometry revision GUID, to provoke recompute
  K5SheetDimension  sheet with one plain linear dimension and no views
"""

import argparse
import datetime
import hashlib
import io
import json
import re
import sys
import uuid
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / 'Rules'))
sys.path.insert(0, str(HERE.parents[4] / 'src'))

import BuildVariants  # noqa: E402
import KitSolids  # noqa: E402

from convert.formats.Fusion.DrawingCodec.Author.BuildBundle import BuildBundle  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Author.BuildDrawing import BuildDrawing  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Author.MakeIdentity import MakeIdentity  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Author.Model.DesignTarget import DesignTarget  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Author.Model.DrawingSpec import DrawingSpec  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Author.Model.SheetSpec import SheetSpec  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Bundle.EmitDrawBundle import EmitDrawBundle  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Bundle.ReadDrawBundle import ReadDrawBundle  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Author.AuthorDwg import AuthorDwg  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Spec.DimensionDraft import DimensionDraft  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Spec.DwgDraft import DwgDraft  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Spec.SheetDraft import SheetDraft  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Spec.TitleText import TitleText  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Spec.ViewDraft import ViewDraft  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Spec.ViewSource import ViewSource  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.EmitDwgFile import EmitDwgFile  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.ReadDwgFile import ReadDwgFile  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Model.DrawingDatabase import DrawingDatabase  # noqa: E402
from convert.formats.Fusion.DrawingCodec.ReadDrawing import ReadDrawing  # noqa: E402

LAYOUT_HANDLE = 0x2E50
MOMENT = datetime.datetime(2026, 11, 12, 12, 0, 0)
GEOMETRY_KEY = re.compile(rb'\x08\x00\x00\x00Geometry\x24\x00\x00\x00((?:[0-9a-f-]\x00){36})')


def field(record, name):
    return next(item.Value for group in record.Groups for item in group.Fields if item.FieldName == name)


def design_target(control):
    """Describe the referenced design from the control drawing's link to it."""
    segment = control.Segments[0]
    records = {(record.ObjectId, record.IsPrimary): record for record in segment.Records}
    link = control.Root.References[0]
    props = dict(link.Properties)
    visible = field(records[(39, True)], 'bodyVisMap').Entries
    instance, component, bodies = visible[0].First.Items
    tracked = field(records[(24, False)], 'children').Items
    scope = field(records[(tracked[0].ObjectId + 3, True)], 'scope').Groups[0].Fields
    brep = records[(tracked[0].ObjectId + 1, True)]
    return DesignTarget(
        DisplayName=props['toDocDisplayName'],
        AssetId=props['linkedAssetGUID'],
        SnapshotId=control.Asset.Links[0].Revision,
        ChangeGuid=control.Asset.ChangeGuid,
        ComponentGuid=scope[1].Value,
        BodyPersistentId=field(brep, 'bodyPersistentId'),
        InstanceId=instance, ComponentId=component, BodiesId=bodies, SketchesId=visible[1].First.Items[2],
        BodyVersion=field(brep, 'version'),
        DesignVersion=int(props['URL'].rsplit('=', 1)[1]),
    )


def geometry_guid(design_bytes):
    with zipfile.ZipFile(io.BytesIO(design_bytes)) as archive:
        for name in archive.namelist():
            if 'FusionACTSegmentType' in name and name.endswith('BulkStream.dat'):
                found = GEOMETRY_KEY.search(archive.read(name))
                if found:
                    return found.group(1).decode('utf-16-le')
    raise ValueError('source design has no body geometry revision')


def views_for(label):
    base = ViewDraft((180.46875, 120.609375), 4.0)
    if label in ('K1SheetOnly', 'K5SheetDimension'):
        return ()
    if label == 'K2BaseView':
        return (base,)
    return (base, ViewDraft((298.0, 120.609375), 4.0, Parent=0), ViewDraft((180.46875, 197.203125), 4.0, Parent=0))


def dimensions_for(label):
    """The base view's bottom edge spans 100.47 to 260.47 mm at y 80.61 mm on the sheet, as in the A1 control."""
    if label in ('K1SheetOnly', 'K2BaseView'):
        return ()
    return (DimensionDraft((260.46875, 80.609375), (100.46875, 80.609375), 70.109375, 4.0),)


def build(label, control, design_bytes, name):
    guid = geometry_guid(design_bytes)
    if label == 'K4StaleViews':
        guid = str(uuid.UUID(int=0))
    source = ViewSource(306, '1_Component', guid, (0.0, 0.0, 0.0), (4.0, 2.0, 1.0), Solid=KitSolids.box_solid((0.0, 0.0, 0.0), (4.0, 2.0, 1.0)))
    layout_name = 'Kit Authored ' + name
    draft = DwgDraft(
        SheetDraft(layout_name, (TitleText('TITLE_1', 'Kit Authored'), TitleText('SHEET', '1/1'), TitleText('DRAWING_NUMBER', name))),
        LAYOUT_HANDLE, MOMENT, str(uuid.uuid4()), str(uuid.uuid4()),
        views_for(label), source if views_for(label) else None, dimensions_for(label),
    )
    with KitSolids.no_edges():
        dwg = AuthorDwg(draft)
    model = ReadDwgFile(dwg)
    if EmitDwgFile(model) != dwg:
        raise ValueError('authored DWG does not read back')
    identity = MakeIdentity()
    spec = DrawingSpec(name, design_target(control), SheetSpec(layout_name), identity, LAYOUT_HANDLE)
    database = DrawingDatabase('ExtFile.' + str(uuid.uuid4()) + '.dwg', dwg)
    drawing = BuildDrawing(spec, database)
    bundle = EmitDrawBundle(BuildBundle(spec, drawing, design_bytes), BuildVariants.compress)
    again = ReadDrawBundle(bundle, BuildVariants.inflate)
    if again.Drawing.Database.Content != dwg:
        raise ValueError('authored bundle does not carry the authored DWG')
    return bundle, dwg, len(model.DwgObjects)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--control', required=True, help='A1 drawing whose link describes the referenced design')
    parser.add_argument('--source', required=True, help='referenced design f3d')
    parser.add_argument('--labels', nargs='+', default=['K1SheetOnly'])
    parser.add_argument('--series', default='K', help='letter that replaces K in the written labels, one letter per authoring round')
    args = parser.parse_args()
    control = ReadDrawing(Path(args.control).read_bytes(), BuildVariants.inflate)
    design_bytes = Path(args.source).read_bytes()
    plan = []
    for label in args.labels:
        name = args.series + label[1:]
        bundle, dwg, count = build(label, control, design_bytes, name)
        label = name
        path = BuildVariants.OUT / f'{label}.f3z'
        path.write_bytes(bundle)
        (BuildVariants.OUT / f'{label}.dwg').write_bytes(dwg)
        plan.append({'label': label, 'file': path.name, 'bytes': len(bundle), 'sha256': hashlib.sha256(bundle).hexdigest(),
                     'dwg_bytes': len(dwg), 'dwg_sha256': hashlib.sha256(dwg).hexdigest(), 'objects': count})
    target = BuildVariants.OUT / 'PlanAuthored.json'
    kept = json.loads(target.read_text())['variants'] if target.exists() else []
    built = {row['label'] for row in plan}
    rows = [row for row in kept if row['label'] not in built] + plan
    target.write_text(json.dumps({'variants': rows}, indent=1) + '\n')
    print(json.dumps(plan, indent=1))


if __name__ == '__main__':
    main()

"""Container-level grafts on the A3 control: Kit's container rules applied to a Fusion-saved drawing.

The control drawing is read with Kit's typed reader, changed in one place and re-emitted with Kit's writer. The
DWG member stays byte for byte as Fusion saved it. M1Reemitted (NativeAcceptance.json) showed that the plain
typed re-emission of this control opens in Fusion with the same measurements, so each variant tests one rule.

* C0Reemitted: no change (repeat of M1Reemitted, the baseline for this round).
* C1NoTemplateThumbs: the template sheet thumbnails (SheetThumbnails/D3_*.png) removed. Kit stops writing them.
* C2NeutralCycle: the drawing component's cyclingColor set to Kit's neutral grey (0.8, 0.8, 0.8), the value
  Kit's design writer already uses. Fusion saves differ here ((78, 150, 188)/255 in the controls and
  (232, 236, 251)/255 in the Wheel drawing), so the value is per document, not a format constant.
* C3Renumbered: the design segment ids after the fixed skeleton renumbered without gaps, in creation order:
  model source 39 and its folder 40 stay, the sheet 43 becomes 41 and the three tracked edges (45, 68 and 74,
  six ids each) become 42, 48 and 54. Every local and segment reference, the class id lists, the stored ids
  and the next id follow. Fusion's own ids have gaps from deleted objects, so this tests whether Kit may number
  per source, per sheet and per tracked edge from one counter.
* C4KitMembers: every F2D member built by Kit's current author (BuildDrawing and BuildBundle) around the control's
  Fusion-saved DWG, as N2AuthoredF2d did before the rules changed. It carries the gapless record ids, the paper
  sheet manifest, no template thumbnails and the neutral component colour together.

Run: python3.14 -I BuildContainer.py --bundle $TMPDIR/KitFusionDrawings/Variants/P0Control.f3z
"""

import argparse
import dataclasses
import hashlib
import json
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / 'Authoring'))

import BuildAuthored  # noqa: E402
import BuildGrafts  # noqa: E402
import BuildHybrid  # noqa: E402
import BuildVariants  # noqa: E402

from convert.formats.Fusion.DrawingCodec.Author.BuildBundle import BuildBundle  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Author.BuildDrawing import BuildDrawing  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Author.MakeIdentity import MakeIdentity  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Author.Model.DrawingSpec import DrawingSpec  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Author.Model.SheetSpec import SheetSpec  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Bundle.EmitDrawBundle import EmitDrawBundle  # noqa: E402
from convert.formats.Fusion.DrawingCodec.EmitDrawing import EmitDrawing  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Model.DrawingDatabase import DrawingDatabase  # noqa: E402
from convert.formats.Fusion.DocumentCodec.Model.ParsedSegment import ParsedSegment  # noqa: E402
from convert.formats.Fusion.DocumentCodec.Records.EmitDocSegment import EmitDocSegment  # noqa: E402
from convert.formats.Fusion.DrawingCodec.ReadDrawing import ReadDrawing  # noqa: E402
from convert.formats.Fusion.SegmentCodec.Metadata.ReadMetaWire import ReadMetaWire  # noqa: E402

PLAN = 'PlanContainer.json'
TEMPLATE_THUMBS = ('SheetThumbnails/D3_large.png', 'SheetThumbnails/D3_small.png')
NEUTRAL = (0.8, 0.8, 0.8)


def without_thumbs(drawing):
    images = tuple(part for part in drawing.Images if not part.Name.endswith(TEMPLATE_THUMBS))
    layout = tuple(slot for slot in drawing.Layout if not slot.Name.endswith(TEMPLATE_THUMBS))
    return dataclasses.replace(drawing, Images=images, Layout=layout), len(drawing.Images) - len(images)


def recoloured(value, hits):
    if type(value).__name__ == 'NamedValue' and value.FieldName == 'cyclingColor' and type(value.Value).__name__ == 'ValueStruct':
        fields = tuple(dataclasses.replace(item, Value=NEUTRAL[('red', 'green', 'blue').index(item.FieldName)]) if item.FieldName in ('red', 'green', 'blue') else item for item in value.Value.Fields)
        hits.append([item.Value for item in value.Value.Fields])
        return dataclasses.replace(value, Value=dataclasses.replace(value.Value, Fields=fields))
    if isinstance(value, tuple):
        return tuple(recoloured(item, hits) for item in value)
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        changes = {}
        for item in dataclasses.fields(value):
            old = getattr(value, item.name)
            new = recoloured(old, hits)
            if new is not old:
                changes[item.name] = new
        return dataclasses.replace(value, **changes) if changes else value
    return value


def renumbered(value, mapping, design):
    kind = type(value).__name__
    if kind == 'LocalRef':
        return dataclasses.replace(value, ObjectId=mapping.get(value.ObjectId, value.ObjectId))
    if kind == 'SegmentRef':
        return dataclasses.replace(value, ObjectId=mapping.get(value.ObjectId, value.ObjectId)) if value.SegmentId == design else value
    if isinstance(value, tuple):
        return tuple(renumbered(item, mapping, design) for item in value)
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        changes = {}
        for item in dataclasses.fields(value):
            old = getattr(value, item.name)
            if kind == 'EntityRecord' and item.name == 'ObjectId':
                new = mapping.get(old, old)
            elif kind == 'MetaClass' and item.name == 'OwnerIds' or kind == 'MetaSegment' and item.name == 'StoredIds':
                new = tuple(mapping.get(number, number) for number in old)
            else:
                new = renumbered(old, mapping, design)
            if new != old or new is not old:
                changes[item.name] = new
        return dataclasses.replace(value, **changes) if changes else value
    return value


def gapless(drawing):
    design = drawing.Segments[0]
    used = sorted({record.ObjectId for record in design.Records})
    mapping, number = {}, 41
    for old in used:
        if old >= 41:
            mapping[old] = number
            number += 1
    segments = []
    for index, segment in enumerate(drawing.Segments):
        meta = renumbered(segment.Metadata, mapping if index == 0 else {}, 0)
        if index == 0:
            meta = dataclasses.replace(meta, NextId=number, Primary=(), Continuations=())
        records = renumbered(segment.Records, mapping if index == 0 else {}, 0)
        if index == 0:
            records = tuple(sorted(records, key=lambda record: (record.ObjectId, not record.IsPrimary)))
        fresh = ParsedSegment(meta, records, segment.Profile)
        streams = EmitDocSegment(fresh)
        final = ReadMetaWire(streams.Metadata, Segment=meta.Header.Segment)
        segments.append(dataclasses.replace(fresh, Metadata=final))
    return dataclasses.replace(drawing, Segments=tuple(segments)), {str(old): new for old, new in mapping.items()}, (design.Metadata.NextId, number)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bundle', required=True)
    args = parser.parse_args()
    out = BuildVariants.OUT
    raw, source = BuildGrafts.bundle_parts(args.bundle)
    drawing = ReadDrawing(raw, BuildVariants.inflate)
    plan = {'route': 'container-level grafts on the A3 control; DWG member untouched', 'variants': []}
    thumbs, dropped = without_thumbs(drawing)
    hits = []
    cycled = dataclasses.replace(drawing, Segments=recoloured(drawing.Segments, hits))
    renumber, mapping, next_ids = gapless(drawing)
    for label, model, note in (('C0Reemitted', drawing, {}), ('C1NoTemplateThumbs', thumbs, {'dropped_images': dropped}),
                               ('C2NeutralCycle', cycled, {'old_colours': hits, 'new_colour': NEUTRAL}),
                               ('C3Renumbered', renumber, {'mapping': mapping, 'next_id': next_ids})):
        emitted = EmitDrawing(model, BuildVariants.compress)
        again = ReadDrawing(emitted, BuildVariants.inflate)
        check = {'images': len(again.Images), 'dwg_same': again.Database == drawing.Database}
        if label == 'C2NeutralCycle':
            seen = []
            recoloured(again.Segments, seen)
            check['read_back_colours'] = seen
        bundle = BuildVariants.typed_bundle(model, source, label)
        path = out / (label + '.f3z')
        path.write_bytes(bundle)
        plan['variants'].append({'label': label, 'file': path.name, 'bytes': len(bundle), 'sha256': hashlib.sha256(bundle).hexdigest(), 'note': note, 'check': check})
    content = drawing.Database.Content
    handle, name = BuildHybrid.sheet_layout(content)
    spec = DrawingSpec('C4KitMembers', BuildAuthored.design_target(drawing), SheetSpec(name), MakeIdentity(), handle)
    kit = BuildDrawing(spec, DrawingDatabase('ExtFile.' + str(uuid.uuid4()) + '.dwg', content))
    bundle = EmitDrawBundle(BuildBundle(spec, kit, source), BuildVariants.compress)
    ids = sorted({record.ObjectId for record in kit.Segments[0].Records})
    path = out / 'C4KitMembers.f3z'
    path.write_bytes(bundle)
    plan['variants'].append({'label': 'C4KitMembers', 'file': path.name, 'bytes': len(bundle), 'sha256': hashlib.sha256(bundle).hexdigest(),
                             'note': {'design_ids': ids, 'next_id': kit.Segments[0].Metadata.NextId, 'images': [part.Name for part in kit.Images], 'sheet': str(kit.Sheet)},
                             'check': {'dwg_same': kit.Database.Content == content}})
    (out / PLAN).write_text(json.dumps(plan, indent=1, default=str) + '\n')
    print(json.dumps([(row['label'], row['note'], row['check']) for row in plan['variants']], default=str))


if __name__ == '__main__':
    main()

import hashlib
import json
import math
import sys
from dataclasses import asdict, replace
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[4]
FOLDER = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))
from convert.formats.Fusion.BrepCodec.Frustum.EmitFrustumHist import EmitFrustumHist
from convert.formats.Fusion.BrepCodec.Frustum.ReadFrustumHist import ReadFrustumHist


def expectations(model):
    bottom, top, height = model.BottomRadius / 10, model.TopRadius / 10, model.Height / 10
    base = tuple(value / 10 for value in model.BasePoint)
    denominator = bottom * bottom + bottom * top + top * top
    offset = height * (bottom * bottom + 2 * bottom * top + 3 * top * top) / (4 * denominator)
    radius = max(bottom, top)
    return dict(
        volume_cm3=math.pi * height * denominator / 3,
        area_cm2=math.pi * (bottom * bottom + top * top) + math.pi * (bottom + top) * math.hypot(height, top - bottom),
        center_cm=[base[0], base[1], base[2] + offset],
        min_cm=[base[0] - radius, base[1] - radius, base[2]],
        max_cm=[base[0] + radius, base[1] + radius, base[2] + height],
    )


def prepare(name, source_name, mode, angle):
    source = ROOT / source_name
    target = FOLDER / (name + '.f3d')
    with ZipFile(source) as archive:
        names = [item for item in archive.namelist() if item.endswith('.smbh')]
        if len(names) != 1:
            raise ValueError('Expected one source history part')
        original = archive.read(names[0])
        value = ReadFrustumHist(original)
        frame = None if mode == 'fresh' else value.Frame
        if mode == 'scale':
            frame = replace(value.Frame, Surface=replace(value.Frame.Surface, ScaleCm=3.125))
        payload = EmitFrustumHist(value.Model, value.Identity, value.TagSet, value.History, value.Stamp, frame)
        with ZipFile(target, 'w') as output:
            for entry in archive.infolist():
                output.writestr(entry, payload if entry.filename == names[0] else archive.read(entry))
    (FOLDER / (name + '.smbh')).write_bytes(payload)
    return dict(
        name=name, mode=mode, source=source_name,
        source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        output=str(target), output_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
        member=names[0], source_history_sha256=hashlib.sha256(original).hexdigest(),
        history_sha256=hashlib.sha256(payload).hexdigest(), history_bytes=len(payload),
        model_mm=asdict(value.Model), identity=asdict(value.Identity), history=asdict(value.History),
        parameter_names=dict(distance='d1', taper='d2'), taper_degrees=angle,
        source_frame=asdict(value.Frame), emitted_frame=None if frame is None else asdict(frame),
        expected=expectations(value.Model),
    )


def main():
    control = 're/Fusion/Study/extents-f0f33a9a605f/taper.f3d'
    holdout = 're/Fusion/Study/holdouts-f8c508a73323/drafted_extrusion.f3d'
    cases = [
        prepare('SourceFrame7deg', control, 'source', 7.0),
        prepare('FreshFrame7deg', control, 'fresh', 7.0),
        prepare('ScaledFrame7deg', control, 'scale', 7.0),
        prepare('HoldoutFrame5deg', holdout, 'source', 5.0),
    ]
    report = dict(scope='Production frustum history reader/writer artifact preparation for native acceptance; only the solved history part is reconstructed, surrounding Design/other members remain from the same source; no native calls or local tests', cases=cases)
    (FOLDER / 'Preparation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps([{key: row[key] for key in ('name', 'output', 'output_sha256', 'history_sha256', 'model_mm', 'parameter_names', 'expected')} for row in cases], indent=2))


if __name__ == '__main__':
    main()

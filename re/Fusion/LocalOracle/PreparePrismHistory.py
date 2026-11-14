import argparse
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time
from zipfile import ZipFile

root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(root / 'src'))

from convert.formats.Fusion.BrepCodec.Models.BodyIdentity import BodyIdentity
from convert.formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from convert.formats.Fusion.BrepCodec.Models.HistoryState import HistoryState
from convert.formats.Fusion.BrepCodec.Models.SketchLink import SketchLink
from convert.formats.Fusion.BrepCodec.Prism.EmitPrismHist import EmitPrismHist
from convert.formats.Fusion.BrepCodec.Prism.Models.PrismLine import PrismLine
from convert.formats.Fusion.BrepCodec.Prism.Models.PrismTags import PrismTags
from convert.formats.Fusion.BrepCodec.Prism.ReadPrismHist import ReadPrismHist
from convert.formats.Fusion.BrepCodec.Prism.Writing.FreshPrism import FreshPrism
from convert.formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp
from convert.formats.Fusion.GeometryCodec.Prism.CuboidBody import CuboidBody

def authored_payload():
    model = CuboidBody(40.0, 30.0, 25.0, (0.0, 0.0, 0.0))
    frame = FreshPrism(model)
    edges = list(frame.Edges)
    for index in (1, 4):
        edge = edges[index]
        origin = frame.CornersCm[edge.EndCorner]
        finish = frame.CornersCm[edge.StartCorner]
        direction = tuple(end - start for start, end in zip(origin, finish, strict=True))
        edges[index] = replace(
            edge, StartCorner=edge.EndCorner, EndCorner=edge.StartCorner,
            Curve=PrismLine(origin, direction),
        )
    frame = replace(frame, Edges=tuple(edges))
    identity = BodyIdentity(0, 301, 7, time.time_ns() / 1000)
    tags = PrismTags(
        tuple(FeatureTag(value, (301,)) for value in ('1', '2', '4', '6', '3', '5')),
        tuple(SketchLink(value, 0, 0, 1, 1) for value in (105, 106, 107, 108)),
    )
    history = HistoryState(4, 2, 4, 1, 2)
    stamp = GeometryStamp('Kit', 'Production prism history', datetime.now(timezone.utc).isoformat())
    return EmitPrismHist(model, identity, tags, history, stamp, frame)

def canonical_payload(data):
    value = ReadPrismHist(data)
    return EmitPrismHist(value.Model, value.Identity, value.TagSet, value.History, value.Stamp, value.Frame)

def prepare(mode):
    source = root / 're/Fusion/Study/thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d'
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    if source_hash != '09980af5a2c9e03e0fc9246ed0b20e796c8f5574c8838d255c85bdd08ea1aa9c':
        raise ValueError('The explicit Design identities require the qualified rectangle control')
    target_dir = root / 're/Fusion/LocalOracle/PrismHistory'
    target_dir.mkdir(parents=True, exist_ok=True)
    reports = []
    for variant in ('canonical', 'authored') if mode == 'both' else (mode,):
        basename = 'HistoryReemitted' if variant == 'canonical' else 'HistoryAuthored'
        target_path = target_dir / f'{basename}.f3d'
        with ZipFile(source) as archive:
            names = [name for name in archive.namelist() if name.endswith('.smbh')]
            if len(names) != 1:
                raise ValueError('Expected exactly one solved history member')
            source_history_hash = hashlib.sha256(archive.read(names[0])).hexdigest()
            payload = authored_payload() if variant == 'authored' else canonical_payload(archive.read(names[0]))
            with ZipFile(target_path, 'w') as target:
                for entry in archive.infolist():
                    target.writestr(entry, payload if entry.filename == names[0] else archive.read(entry))
        standalone = target_dir / f'{basename}.smbh'
        standalone.write_bytes(payload)
        reports.append({
            'variant': variant, 'source': str(source.relative_to(root)),
            'source_sha256': source_hash, 'output': str(target_path.relative_to(root)),
            'source_history_sha256': source_history_hash,
            'output_sha256': hashlib.sha256(target_path.read_bytes()).hexdigest(),
            'history': str(standalone.relative_to(root)), 'history_member': names[0],
            'history_bytes': len(payload), 'history_sha256': hashlib.sha256(payload).hexdigest(),
            'geometry_mm': {'width': 40, 'depth': 30, 'height': 25, 'base': [0, 0, 0]},
            'expected_volume_cm3': 30.0, 'expected_topology': {'faces': 6, 'edges': 12, 'vertices': 8},
            'scope': 'Only the complete solved history is rewritten; surrounding Design and snapshot remain this source document',
            'construction': 'Explicit dimensions, identities and journal states with fresh topology and source-CCW carrier directions; no history payload input' if variant == 'authored' else 'Production typed read followed by canonical record allocation and complete reserialization',
            'native_acceptance': 'not performed by this preparation script',
        })
        report_name = 'Preparation.json' if variant == 'canonical' else 'AuthoredPreparation.json'
        (target_dir / report_name).write_text(json.dumps(reports[-1], indent=2) + '\n')
    print(json.dumps(reports, indent=2))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=('canonical', 'authored', 'both'), default='both')
    arguments = parser.parse_args()
    prepare(arguments.mode)

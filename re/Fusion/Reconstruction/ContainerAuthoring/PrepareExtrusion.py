import argparse
import hashlib
import json
import runpy
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
REPOSITORY = BASE.parents[3]
sys.path.insert(0, str(REPOSITORY / 'src'))

from convert.formats.Fusion.BrepCodec.EmitHistory import EmitHistory
from convert.formats.Fusion.BrepCodec.Models.BodyIdentity import BodyIdentity
from convert.formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from convert.formats.Fusion.BrepCodec.Models.HistoryState import HistoryState
from convert.formats.Fusion.BrepCodec.Models.SketchLink import SketchLink
from convert.formats.Fusion.BrepCodec.Models.TopologyTags import TopologyTags
from convert.formats.Fusion.GeometryCodec.CylinderBody import CylinderBody
from convert.formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp

AUTHOR = runpy.run_path(str(BASE / 'AuthorFeatureContainer.py'))


def encode_history(contract, authored_at):
    parsed = datetime.fromisoformat(authored_at.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('Authoring timestamp requires a timezone')
    micros = int(parsed.timestamp() * 1_000_000)
    model = CylinderBody(contract['radiusMillimeters'], contract['heightMillimeters'], (0.0, 0.0, 0.0))
    identity = BodyIdentity(contract['bodyKey'], contract['operationId'], contract['generationRef'], float(micros))
    operations = (contract['operationId'],)
    tags = TopologyTags(
        FeatureTag(contract['sideFaceLabel'], operations),
        FeatureTag(contract['topFaceLabel'], operations),
        FeatureTag(contract['bottomFaceLabel'], operations),
        FeatureTag(contract['topEdgeLabel'], operations),
        FeatureTag(contract['bottomEdgeLabel'], operations),
        SketchLink(contract['sketchPrimary'], 0, 0, 1, 1),
    )
    history_fields = dict(contract)
    for old, new in (('historyGeneration', 'historyCurrentStateId'), ('allocation', 'nextEntityTag'), ('boardNumber', 'boardStatus')):
        if old in history_fields:
            if new in history_fields:
                raise ValueError('Conflicting legacy history contract names')
            history_fields[new] = history_fields.pop(old)
    history = HistoryState(contract['currentHistoryId'], contract['initialHistoryId'], history_fields['historyCurrentStateId'], history_fields['nextEntityTag'], history_fields['boardStatus'], history_fields.get('maxStateId'))
    stamp = GeometryStamp('Kit', 'Independent authored extrusion', parsed.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z'))
    data = EmitHistory(model, identity, tags, history, stamp)
    evidence = {'encoder': 'convert.formats.Fusion.BrepCodec.EmitHistory.EmitHistory', 'cylinder': asdict(model), 'bodyIdentity': asdict(identity), 'topologyTags': asdict(tags), 'history': asdict(history), 'stamp': asdict(stamp), 'partName': contract['partName'], 'bodyEntityId': contract['bodyEntityId'], 'bodyUuidInDesign': contract['bodyUuid'], 'size': len(data), 'sha256': hashlib.sha256(data).hexdigest(), 'sourceGeometry': None, 'sourceHistory': None}
    return data, evidence


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--specification', type=Path, default=BASE.parent / 'DocumentAuthoring' / 'Variants' / 'ExtrudeSpecification.json')
    parser.add_argument('--output', type=Path, default=BASE / 'FreshExtrusion')
    parser.add_argument('--authored-at', default=datetime.now(timezone.utc).isoformat())
    arguments = parser.parse_args()
    design = AUTHOR['prepare_feature']('extrude', json.loads(arguments.specification.read_text()))
    data, evidence = encode_history(design['model']['brepContract'], arguments.authored_at)
    result = AUTHOR['package_feature'](design, brep_encoder=lambda contract: data)
    report = AUTHOR['write_result'](design, result, arguments.output, 'extrude')
    (arguments.output / 'AuthoredHistory.smbh').write_bytes(data)
    (arguments.output / 'BrepEncoding.json').write_text(json.dumps(evidence, indent=2) + '\n')
    report['brepEncoding'] = evidence
    report['specificationSource'] = str(arguments.specification)
    (arguments.output / 'Generation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()

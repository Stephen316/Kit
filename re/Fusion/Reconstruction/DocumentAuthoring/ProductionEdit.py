import hashlib
import json
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'src'))
sys.dont_write_bytecode = True


def main():
    from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
    from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed

    source_path = ROOT / 're/Fusion/LocalOracle/Authored/ProductionExtrusion.f3d'
    output_path = source_path.with_name('ProductionEdited.f3d')
    source = source_path.read_bytes()
    model = ReadDocument(source)
    changed = []
    segments = []
    for segment in model.Segments:
        records = []
        for record in segment.Records:
            groups = []
            for group in record.Groups:
                fields = []
                for field in group.Fields:
                    if field.FieldName == 'comment' and field.Value == 'Production native codec acceptance':
                        changed.append({'entityId': record.ObjectId, 'classIdentifier': group.ClassGuid, 'field': field.FieldName, 'before': field.Value, 'after': 'Edited through complete typed document model'})
                        field = replace(field, Value='Edited through complete typed document model')
                    fields.append(field)
                groups.append(replace(group, Fields=tuple(fields)))
            records.append(replace(record, Groups=tuple(groups)))
        segments.append(replace(segment, Records=tuple(records)))
    if len(changed) != 1:
        raise ValueError('Expected exactly one named user parameter comment')
    result = EmitParsed(replace(model, Segments=tuple(segments)))
    output_path.write_bytes(result)
    report = {'schema': 'FusionProductionSemanticEdit/1', 'sourceSha256': hashlib.sha256(source).hexdigest(), 'outputSha256': hashlib.sha256(result).hexdigest(), 'changes': changed, 'decodedSegments': len(model.Segments), 'decodedRecords': sum(len(segment.Records) for segment in model.Segments), 'typedHistoryParts': len(model.Bodies), 'sourceEntityPayloadsRetained': False, 'sourceHistoryPayloadsRetained': False, 'nativeAcceptance': 'pending'}
    output_path.with_suffix('.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()

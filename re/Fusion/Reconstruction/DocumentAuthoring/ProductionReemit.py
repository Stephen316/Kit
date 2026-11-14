import argparse
import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'src'))
sys.dont_write_bytecode = True


def main():
    from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
    from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed

    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    source = arguments.source.read_bytes()
    model = ReadDocument(source)
    result = EmitParsed(model)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_bytes(result)
    report = {'schema': 'FusionProductionDocumentReemit/1', 'nativeAcceptance': 'pending', 'sourceSha256': hashlib.sha256(source).hexdigest(), 'outputSha256': hashlib.sha256(result).hexdigest(), 'sourceBytes': len(source), 'outputBytes': len(result), 'segmentCount': len(model.Segments), 'entityRecordCount': sum(len(segment.Records) for segment in model.Segments), 'historyPartCount': len(model.Bodies), 'runtimeSourcePayloadCopy': False, 'bodies': [{'radiusMillimeters': body.History.Model.Radius, 'heightMillimeters': body.History.Model.Height, 'baseMillimeters': body.History.Model.BasePoint} for body in model.Bodies]}
    arguments.output.with_suffix('.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()

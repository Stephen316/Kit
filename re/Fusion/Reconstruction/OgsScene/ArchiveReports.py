import hashlib
import json
import lzma
from pathlib import Path

BASE = Path(__file__).resolve().parent


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    artifacts = []
    for name in ('SerializerCalls', 'DecodedSamples'):
        raw = (BASE / (name + '.json')).read_bytes()
        compressed = lzma.compress(raw, preset=9)
        target = BASE / (name + '.json.xz')
        target.write_bytes(compressed)
        artifacts.append({'path': target.name, 'sha256': digest(compressed), 'decodedSha256': digest(raw), 'decodedBytes': len(raw)})
    samples = json.loads((BASE / 'DecodedSamples.json').read_text())
    summary = {'artifacts': artifacts, 'sources': [{'source': row['source'], 'sourceSha256': row['sourceSha256'], 'worldBytes': row['world']['size'], 'worldSha256': row['world']['sha256'], 'worldFields': len(row['world']['fields']), 'worldConsumed': row['world']['decodedPrefixEnd'], 'worldUnresolved': row['world']['unresolved'], 'meshBytes': row['mesh']['size'], 'meshSha256': row['mesh']['sha256'], 'meshUnaddressed': row['mesh']['unaddressedSpans'], 'simpleMeshes': len(row['world']['isolatedMeshCandidates'])} for row in samples['sources']], 'verification': 'Static binary research and direct archive decoding only; no production execution, local automated tests or native re-emission acceptance'}
    (BASE / 'EvidenceIndex.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary['sources'], indent=2))


if __name__ == '__main__':
    main()

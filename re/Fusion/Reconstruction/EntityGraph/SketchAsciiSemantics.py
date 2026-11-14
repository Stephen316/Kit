import collections
import hashlib
import json
import lzma
import runpy
import sys
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
DECODER = runpy.run_path(str(BASE.parent / 'BrepTokens.py'))['read_stream']


def corpus():
    inventory_path = BASE.parent / 'BrepCoverage/Inventory.json.xz'
    inventory = json.loads(lzma.decompress(inventory_path.read_bytes()))
    seen = set()
    versions = collections.Counter()
    directions = collections.Counter()
    flags = collections.Counter()
    splits = collections.Counter()
    secondary_ids = collections.Counter()
    examples = []
    example_keys = set()
    outside = []
    total = 0
    largest_primary = 0
    for entry in inventory['members']:
        if entry['sha256'] in seen:
            continue
        seen.add(entry['sha256'])
        with zipfile.ZipFile(ROOT / entry['path']) as archive:
            payload = archive.read(entry['member'])
        if hashlib.sha256(payload).hexdigest() != entry['sha256']:
            raise ValueError('Source member digest changed')
        parsed = DECODER(payload)
        for record in parsed['records']:
            if record['name'] != 'ATTRIB_CUSTOM-attrib':
                continue
            values = [item['value'] for item in record['fields']]
            if values[5] != 'sketch_attrib_def':
                continue
            versions[values[8]] += 1
            if values[8] != 3:
                continue
            if len(values) != 10:
                raise ValueError('Unexpected ASCII sketch attribute layout')
            parts = [int(part) for part in values[9].split(' ')]
            if len(parts) != 6:
                raise ValueError('ASCII sketch attribute lacks six fields')
            primary, secondary, direction, roleflags, sequence, count = parts
            total += 1
            largest_primary = max(largest_primary, primary)
            directions[direction] += 1
            flags[roleflags] += 1
            splits[(sequence, count)] += 1
            secondary_ids[secondary] += 1
            invalid = not (0 <= primary < 1 << 64 and 0 <= secondary < 1 << 64 and 0 <= roleflags < 1 << 64 and direction in (0, 1, 4294967295) and 1 <= sequence <= count < 1 << 32)
            sample = dict(path=entry['path'], member=entry['member'], sha256=entry['sha256'], physicalRecordIndex=record['physical_record_index'], byteOffset=record['offset'], text=values[9])
            if invalid:
                outside.append(sample)
            example_key = (bool(secondary), roleflags, sequence, count, direction)
            if (roleflags or secondary or (sequence, count) != (1, 1) or direction == 4294967295) and example_key not in example_keys and len(examples) < 24:
                example_keys.add(example_key)
                examples.append(sample)
    return dict(scope='Every sketch attribute including archived revisions in each distinct ASM blob; repeated member digests counted once', sourceInventorySha256=hashlib.sha256(inventory_path.read_bytes()).hexdigest(), distinctBlobs=len(seen), versionCounts=dict(versions), asciiAttributes=total, maximumPrimaryId=largest_primary, secondaryIdCounts=dict(secondary_ids), directionCounts=dict(directions), roleFlagsCounts=dict(flags), splitPairs=[dict(sequence=key[0], total=key[1], count=value) for key, value in sorted(splits.items())], nontrivialExamples=examples, outsideSemanticDomain=outside)


def main():
    names = ('primaryId', 'secondaryId', 'direction', 'topologyRoleFlags', 'splitSequenceId', 'splitTotalNumber')
    report = dict(schema='FusionSketchAsciiSemantics/1', method='Read-only raw corpus token inspection; no native calls, product execution or tests. Field names follow the saved Design sketch tag record. The earlier static library inspection was removed.', asciiFields=[dict(position=index, name=name) for index, name in enumerate(names, 1)], binaryStreamerOrder=['version', 'primaryId', 'secondaryId', 'direction', 'splitSequenceId', 'splitTotalNumber', 'topologyRoleFlags'], qualifiedDomain=dict(primaryId='uint64 storage; source-key allocation semantics separately qualified', secondaryId='uint64 storage; existing authored ordinary sketch profile zero', direction=[0, 1, 4294967295], topologyRoleFlags='uint64 mask; existing ordinary authored profile zero; complete named bit dictionary unresolved', split='1 <= splitSequenceId <= splitTotalNumber <= UINT32_MAX'), semanticEvidence=['SketchSplitSemantics.json'], caveats=['Split sequence and total are ordinal/count, not two unrelated enums', 'ASCII version3 and the fixed binary Design record use different member orders', 'The corpus holds only version3 ASCII attributes; older kernel forms are not observed', 'Mapping the fourth ASCII field to topologyRoleFlags came from removed static evidence; the corpus shows it as zero in every attribute; not confirmed by a black-box experiment', 'Storage widths follow the saved Design sketch tag record; the ASCII text alone does not fix them', 'topologyRoleFlags is a behavior-based name; complete bit meanings remain unresolved'], corpus=corpus())
    report['directionReversal'] = dict(proposedMapping={'0': 1, '1': 0, '4294967295': 4294967295}, evidenceClass='Proposal only; it came from removed static evidence and is not confirmed by a black-box experiment')
    output = BASE / 'SketchAsciiSemantics.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report['corpus'], indent=2))


if __name__ == '__main__':
    main()

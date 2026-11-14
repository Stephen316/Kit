import collections
import hashlib
import json
import lzma
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / 're/Fusion/Reconstruction/BrepCoverage/Inventory.json.xz'
BASE_KINDS = {'asmheader', 'body', 'lump', 'shell', 'face', 'loop', 'coedge', 'edge', 'vertex', 'point', 'plane-surface', 'cone-surface', 'ellipse-curve', 'straight-curve', 'ATTRIB_CUSTOM-attrib'}
BASE_ATTRIBUTES = {'Timestamp_attrib_def', 'generic_tag_attrib_def', 'sketch_attrib_def', 'FPM_tracked_attrib_def'}


def summarize(rows):
    return dict(members=len(rows), archives=len({item['path'] for item in rows}), uniqueBlobs=len({item['sha256'] for item in rows}), histories=sum(item['extension'] == '.smbh' for item in rows), snapshots=sum(item['extension'] == '.smb' for item in rows))


def main():
    data = json.loads(lzma.decompress(SOURCE.read_bytes()))
    members, blobs = data['members'], data['uniqueBlobs']
    missing = collections.defaultdict(list)
    known = []
    types = collections.Counter()
    attributes = collections.Counter()
    expansions = {}
    plans = (
        ('known-kind-vocabulary', set(), set()),
        ('plus-transform', {'transform'}, set()),
        ('plus-transform-sphere-torus', {'transform', 'sphere-surface', 'torus-surface'}, set()),
        ('plus-fdm-attribute', {'transform', 'sphere-surface', 'torus-surface'}, {'FDM_feature_attrib_def'}),
    )
    for member in members:
        blob = blobs[member['sha256']]
        types.update(blob['recordTypes'])
        attributes.update(blob['attributeTypes'])
        absent = tuple(sorted(set(blob['recordTypes']) - BASE_KINDS))
        attrs = tuple(sorted(set(blob['attributeTypes']) - BASE_ATTRIBUTES))
        missing[(absent, attrs)].append(member)
        if not absent and not attrs:
            known.append(member)
    for label, kinds, attrs in plans:
        rows = [item for item in members if set(blobs[item['sha256']]['recordTypes']) <= BASE_KINDS | kinds and set(blobs[item['sha256']]['attributeTypes']) <= BASE_ATTRIBUTES | attrs]
        complete = [path for path in {item['path'] for item in rows} if all(item in rows for item in members if item['path'] == path)]
        expansions[label] = {**summarize(rows), 'archivesWhoseEveryBrepInitialTableMeetsVocabulary': len(complete)}
    planar = [item for item in known if blobs[item['sha256']]['bodies'] and all(body.get('planarLinearCandidate') for body in blobs[item['sha256']]['bodies'])]
    single = [item for item in planar if item['extension'] == '.smbh' and len(blobs[item['sha256']]['bodies']) == 1]
    nonbox = [item for item in single if not blobs[item['sha256']]['bodies'][0].get('axisAlignedBoxCandidate')]
    report = dict(schema='FusionNextGeometryVocabulary/1', source='re/Fusion/Reconstruction/BrepCoverage/Inventory.json.xz', sourceSha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(), scope='Reuse of all 1170 indexed BRep initial tables; vocabulary and existing ownership evidence only, not product reader execution or semantic/native acceptance', totals=summarize(members), initialRecordTypes=dict(types.most_common()), initialAttributeTypes=dict(attributes.most_common()), additiveVocabularyCandidates=expansions, knownPlanarTables=summarize(planar), oneBodyPlanarHistories=summarize(single), oneBodyNonboxPlanarHistories=summarize(nonbox), smallestNonboxExamples=[{**item, 'body': blobs[item['sha256']]['bodies'][0], 'historyRecordTypes': blobs[item['sha256']]['historyRecordTypes']} for item in sorted(nonbox,key=lambda item:item['size'])[:8]], missingKindGroups=[dict(recordKinds=list(key[0]), attributeKinds=list(key[1]), **summarize(rows), smallestExample=min(rows,key=lambda item:item['size'])) for key,rows in sorted(missing.items(), key=lambda item: -len(item[1]))])
    target=Path(__file__).with_name('GeometryCoverage.json')
    target.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({key:report[key] for key in ('totals','additiveVocabularyCandidates','knownPlanarTables','oneBodyPlanarHistories','oneBodyNonboxPlanarHistories')},indent=2))


if __name__ == '__main__':
    main()

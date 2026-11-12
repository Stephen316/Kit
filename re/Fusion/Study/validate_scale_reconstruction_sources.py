"""Focused native source proof and malformed guards; no main or live calls."""
import argparse
import copy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import struct

from decode_scale_reconstruction_sources import qualify_scale_reconstruction_sources, SCALE
from decode_sketch import attributes, reference
from validate_mesh_remesh import load

ROOT = Path(__file__).resolve().parent
BASELINE = Path('/private/tmp/fusion-scale-reconstruction-baseline.json')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(zstd, baseline_path=BASELINE):
    baseline = json.loads(baseline_path.read_text())
    assert baseline['baseline_commit'] == 'fb2865a'
    samples, checks, guards, positives = [], [], [], []
    source_count = line_count = point_count = coedge_count = 0
    saved = None

    def check(label, value):
        if not value:
            raise AssertionError(label)
        checks.append(label)

    for ordinal, (archive, before) in enumerate(zip(baseline['files'],baseline['before'])):
        data,records,features,member,members = load(ROOT,archive,zstd)
        bindings = before['streams'][0]['body_blob_bindings']
        original = copy.deepcopy((features,bindings))
        scales = [f for f in features if f.get('class_guid') == SCALE]
        sources, unresolved = [], []
        for feature in scales:
            try:
                result = qualify_scale_reconstruction_sources(data,records,features,member,members,bindings,feature)
            except ValueError as error:
                unresolved.append(dict(feature_object_id=feature['object_id'],reason=str(error)))
            else:
                if result is not None:
                    sources.append(result)
        check(archive+' caller metadata unchanged',(features,bindings) == original)
        entry = dict(archive=archive,archive_sha256=sha(ROOT/archive),expected_sources=sources,expected_unresolved=unresolved)
        if ordinal >= 7:
            check(archive+' explicitly unsupported Scale or outside family', not sources
                and (len(unresolved) == 1 if ordinal < 10 else not unresolved))
            samples.append(entry)
            continue
        check(archive+' one qualified native Scale owner',len(sources) == 1 and not unresolved)
        row = sources[0]
        check(archive+' no invented Scale result/state identities',row['scale_owned_result_anchors'] == []
            and row['API_handle_identity'] is None and row['persistent_identity'] is None
            and row['qualified_historical_state'] is None)
        check(archive+' finite factors and center from explicit native fields',len(row['settings']['factors_xyz']) == 3
            and len(row['settings']['reconstruction_center_cm']) == 3
            and row['settings']['reconstruction_center_cm'] == row['point_provenance']['center_position_cm'])
        by = {r.object_id:r for r in records if r.is_primary}
        for group in row['source_groups']:
            source_count += 1
            anchor = by[group['body_anchor_object_id']]
            raw_anchor = data[anchor.body:anchor.end]
            check(archive+' explicit anchor owner/BODY refs '+str(anchor.object_id),
                reference(raw_anchor,80) == group['native_body_object_id']
                and reference(raw_anchor,91) == group['source_feature_object_id']
                and group['source_anchor']['source_owner_object_id'] != row['feature_object_id'])
            controls = group['extrude_controls']
            check(archive+' common Extrude geometry controls '+str(anchor.object_id),
                controls['operation']['kind'] == 'NewBody' and controls['is_solid'] is True
                and controls['start']['kind'] == 'ProfilePlane' and controls['extent']['mode'] == 'OneSided'
                and controls['extent']['side_one']['condition'] == 'Distance'
                and controls['extent']['side_one']['taper_angle_radians'] == 0)
            correspondence = group['profile_cache_correspondence']
            check(archive+' complete source profile identity '+str(anchor.object_id),
                correspondence['source_feature_object_id'] == group['source_feature_object_id']
                and correspondence['native_body_object_id'] == group['native_body_object_id']
                and correspondence['asm_body_index'] == group['asm_body_index']
                and len(correspondence['source_curves']) == 4)
            points = {p['point_object_id']:p for p in group['native_profile_points']}
            degree = {identity:0 for identity in points}
            for line in group['native_profile_lines']:
                native = by[line['line_object_id']]
                raw = data[native.body:native.end]
                props,cursor = attributes(raw,2)
                check(archive+' native Line endpoint/tag IDs '+str(native.object_id),
                    props['crv_primary_id'] == line['entity_tag']
                    and reference(raw,cursor+107) == line['start_point_id']
                    and reference(raw,cursor+96) == line['end_point_id']
                    and reference(raw,len(raw)-11) == group['source_sketch']['sketch_object_id'])
                degree[line['start_point_id']] += 1
                degree[line['end_point_id']] += 1
                line_count += 1
            for point in points.values():
                native = by[point['point_object_id']]
                raw = data[native.body:native.end]
                props,cursor = attributes(raw,2)
                check(archive+' native POINT payload '+str(native.object_id),
                    props['pt_tag'] == point['entity_tag']
                    and list(struct.unpack_from('<3d',raw,cursor+19)) == point['position_cm']
                    and reference(raw,len(raw)-11) == group['source_sketch']['sketch_object_id'])
                point_count += 1
            check(archive+' four distinct POINTs with two native Line incidences each '+str(anchor.object_id),
                len(points) == 4 and set(degree.values()) == {2})
            coedge_count += sum(len(curve['cached_coedge_candidates']) for curve in correspondence['source_curves'])
            check(archive+' mapping is stored-ID proof independent of old ordinal guesses '+str(anchor.object_id),
                group['binding']['asm_stored_entity_id'] == group['binding']['stored_handle']
                and group['binding']['previous_ordinal_candidate'] is None)
        check(archive+' center/source component ownership',row['component_provenance']['component_object_id'] == 3
            and all(r['component_object_id'] == 3 for r in row['component_provenance']['dependency_scopes']))
        if 'scale_vertex' in archive:
            point = row['point_provenance']
            check(archive+' missing initial vertex names retained without coordinate fallback',
                point['initial_cache_vertex_identity'] is None
                and not point['initial_cache_incidence']['associations']
                and point['initial_cache_incidence']['unresolved'])
        if saved is None:
            saved = data,records,features,member,members,bindings,scales[0],row
        samples.append(entry)

    data,records,features,member,members,bindings,feature,row = saved
    by = {r.object_id:r for r in records if r.is_primary}

    def reject(label, changed_data=data, changed_records=records, changed_features=None, changed_bindings=None):
        fs = features if changed_features is None else changed_features
        bb = bindings if changed_bindings is None else changed_bindings
        ms = dict(members)
        ms[member] = changed_data
        try:
            qualify_scale_reconstruction_sources(changed_data,changed_records,fs,member,ms,bb,
                next(f for f in fs if f['object_id'] == feature['object_id']))
        except ValueError as error:
            guards.append(dict(label=label,reason=str(error)))
        else:
            raise AssertionError(label+' did not reject')

    def altered(offset, value):
        raw = bytearray(data)
        raw[offset:offset+len(value)] = value
        return bytes(raw)

    group = row['source_groups'][0]
    first_line = group['native_profile_lines'][0]
    line = by[first_line['line_object_id']]
    _,cursor = attributes(data[line.body:line.end],2)
    reject('Duplicate primary native source Line',changed_records=records+[line])
    reject('Native Line endpoint ID inconsistent with its representation',
        changed_data=altered(line.body+cursor+108,struct.pack('<Q',first_line['end_point_id'])))
    source = by[group['source_feature_object_id']]
    reject('Source operation cannot become Join',changed_data=altered(source.body+9,struct.pack('<I',1)))
    loop = by[group['profile_cache_correspondence']['profile_loop_definition_object_id']]
    reject('Profile tag cannot choose another curve by coordinates',changed_data=altered(loop.body+29,struct.pack('<Q',999999)))
    fake = copy.deepcopy(features)
    next(f for f in fake if f['object_id'] == feature['object_id'])['parameters'][0]['raw_float64'] += .5
    reject('Caller Scale parameter mutation disagrees with native reciprocal binding',changed_features=fake)
    fake = copy.deepcopy(bindings)
    fake['decoded'][0]['bindings'][0]['stored_handle'] += 999
    reject('Forged native mapping handle cannot become a BODY association',changed_bindings=fake)
    raw_anchor = by[group['body_anchor_object_id']]
    reject('Historical anchor owner cannot become receiving Scale',
        changed_data=altered(raw_anchor.body+92,struct.pack('<Q',feature['object_id'])))
    receiver = by[feature['object_id']]
    receiver_payload = data[receiver.body:receiver.end]
    native_label = struct.pack('<I',5)+'Scale'.encode('utf-16le')
    check('Native receiving Scale label has one exact bounded location',receiver_payload.count(native_label) == 1)
    label_offset = receiver_payload.index(native_label)+4
    reject('Missing fresh native receiver label becomes explicit unsupported diagnostic',
        changed_data=altered(receiver.body+label_offset,b'X'))
    reject('Center backend owner cannot become source Extrude',changed_data=altered(
        by[row['point_provenance']['backend']['object_id']].body+168,struct.pack('<Q',source.object_id)))

    fake_features = copy.deepcopy(features)
    for item in fake_features:
        item['harmless_later_annotation'] = dict(not_native=True)
        if item['kind'] == 'Sketch':
            item['geometry'] = [dict(kind='BogusCallerGeometry',object_id=-1)]
            item['placement'] = dict(sketch_to_component_matrix=[999.]*16)
    fake_bindings = copy.deepcopy(bindings)
    for mapped in fake_bindings['decoded']:
        for item in mapped['bindings']:
            item.update(candidate_asm_body_index=999999,name='Caller label')
    enriched = qualify_scale_reconstruction_sources(data,records,fake_features,member,members,fake_bindings,
        next(f for f in fake_features if f['object_id'] == feature['object_id']))
    check('Source proof independent of caller Sketch geometry/placement/ordinal/display annotations',enriched == row)
    positives.append(dict(label='Ignored caller annotations; fresh native source dictionary exact',passed=True))
    return dict(interface='qualify_scale_reconstruction_sources(data,records,features,member,members,body_blob_bindings,feature)',
        scope='Fresh native source-route/controls/profile identity proof; C separately fixes cache vertices and derives Scale geometry. No main/live calls.',
        baseline=dict(commit='fb2865a',path=str(baseline_path),sha256=sha(baseline_path)),
        samples=samples,guards=guards,positive_controls=positives,checks=checks,
        source_sha256={name:sha(ROOT/name) for name in ('decode_scale_reconstruction_sources.py',
            'validate_scale_reconstruction_sources.py','decode_profile_cache_correspondence.py',
            'decode_body_tools.py','decode_body_tool_selections.py','decode_scale_inputs.py',
            'decode_extrude.py','decode_sketch.py','decode_placement.py','decode_body_asm_identifiers.py')},
        validation=dict(positive_owners=7,source_BODY_groups=source_count,native_profile_lines=line_count,
            native_profile_points=point_count,retained_COEDGE_candidates=coedge_count,
            unsupported_Scale_controls=3,outside_family_controls=2,focused_checks=len(checks),
            negative_guards=len(guards),positive_controls=len(positives),main_reader_calls=0,live_API_calls=0))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline',type=Path,default=BASELINE)
    parser.add_argument('--zstd-library',default=str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib'))))
    parser.add_argument('--output',type=Path,default=ROOT/'scale-reconstruction-source-decoding.json')
    args = parser.parse_args()
    report = validate(args.zstd_library,args.baseline)
    args.output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps(report['validation'],sort_keys=True))

"""Focused saved-file BaseMesh provenance proof; no main-reader or live calls."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from decode_base_mesh_feature_definitions import decode_base_mesh_feature_definitions
from decode_base_mesh_sources import decode_base_mesh_sources
from decode_mesh_geometry_variants import decode_mesh_contents_variants
from decode_retained_mesh_sources import decode_retained_mesh_record, decode_retained_mesh_source
from validate_mesh_remesh import load

ROOT = Path(__file__).resolve().parent
FILES = (
    'meshconverts-4b42d39fb1d5/faceted_closed.f3d',
    'meshconverts-4b42d39fb1d5/faceted_open.f3d',
    'meshcombines-541ebb6cc93f/cut.f3d',
    'meshcombines-541ebb6cc93f/intersect.f3d',
    'meshcombines-541ebb6cc93f/join.f3d',
    'meshseparates-41126250c03f/connected_shell_control.f3d',
    'meshseparates-41126250c03f/two_face_groups.f3d',
    'meshseparates-41126250c03f/two_shells.f3d',
    'meshremoves-8b2188cd274d/one_remove_one.f3d',
    'meshremoves-8b2188cd274d/two_remove_both.f3d',
    'meshremoves-8b2188cd274d/two_remove_first.f3d',
    'meshconvertoperations-5af73924aa60/two_mesh_parametric.f3d',
    'meshcontrasts-10c2557c91a3/stl_centimeter.f3d',
    'meshcontrasts-10c2557c91a3/stl_millimeter.f3d',
    'meshcontrasts-10c2557c91a3/triangle_data_centimeter.f3d',
    'patchcontinuity-b9b0be85a281/brep_tangent.f3d')


def validate(root, zstd, prior_cache):
    prior = json.loads(prior_cache.read_text())
    prior_by = {Path(row['file']).relative_to(root).as_posix(): row for row in prior}
    report = dict(scope='Typed saved BaseMesh source provenance only; no parent BaseFeature, visibility, API handle assignment or lifecycle inference',
        interface='decode_base_mesh_sources(data,records,features,member,members,*,definitions=None,mesh_contents=None)->partial/unresolved/scope',
        prior_cache=dict(path=str(prior_cache), sha256=hashlib.sha256(prior_cache.read_bytes()).hexdigest(),
                         scope='Previously saved193 outputs; this validator does not regenerate main outputs'),
        samples=[], legacy_selected_source_controls=[], guards=[], API_counterexamples=[],
        source_sha256={name: hashlib.sha256((root/name).read_bytes()).hexdigest() for name in (
            'decode_base_mesh_sources.py', 'decode_base_mesh_feature_definitions.py',
            'decode_retained_mesh_sources.py', 'decode_mesh_contents.py', 'decode_mesh_geometry_variants.py',
            'decode_mesh_selections.py', 'validate_base_mesh_sources.py')})
    loaded = {}
    for archive in FILES:
        data, records, features, member, members = load(root, archive, zstd)
        loaded[archive] = (data, records, features, member, members)
        before = copy.deepcopy(features)
        definitions = decode_base_mesh_feature_definitions(data, records, features)
        meshes = decode_mesh_contents_variants(data, records, member, members)
        stream = next(s for s in prior_by[archive]['streams'] if s['member'] == member)
        if 'mesh_contents' in stream:
            assert meshes == stream['mesh_contents'], archive
        else:
            assert not meshes['decoded'] and not meshes['unresolved'], archive
        summary = decode_base_mesh_sources(data, records, features, member, members,
                                          definitions=definitions, mesh_contents=meshes)
        assert not summary['unresolved'], (archive, summary)
        assert features == before, archive
        for row in summary['partial']:
            assert all(row[key] is None for key in (
                'parent_base_feature_object_id', 'API_handle_assignment', 'visibility',
                'qualified_historical_state', 'lifecycle'))
            if row['relationship_kind'] == 'RetainedStoredMeshRoute':
                retained = row['retained_stored_mesh']
                assert row['mesh_object_id'] not in retained['retained_owner_collection_member_ids']
                assert retained['base_mesh_feature_object_id'] == row['feature_object_id']
            else:
                assert row['mesh_object_id'] in row['current_mesh_route']['collection_mesh_object_ids']
        report['samples'].append(dict(archive=archive,
            archive_sha256=hashlib.sha256((root/archive).read_bytes()).hexdigest(),
            expected_decoded=summary, expected_prior_mesh_contents=stream.get('mesh_contents'),
            existing_mesh_diagnostics_unchanged=True, input_features_unchanged=True))

    # Full old dictionaries, not merely source IDs, preserve the selected-source
    # wrapper's established selection qualification and exact scope strings.
    for name in ('mesh-convert-decoding.json', 'mesh-combine-decoding.json', 'mesh-remove-decoding.json'):
        evidence = json.loads((root/name).read_text())
        for sample in evidence['samples']:
            archive = sample['archive']
            if archive not in loaded:
                continue
            for row in sample['expected_decoded']['decoded']:
                settings = row['settings']
                if name == 'mesh-convert-decoding.json':
                    pairs = [(settings['source_mesh_selection'], settings['qualified_source_mesh'])]
                elif name == 'mesh-combine-decoding.json':
                    pairs = list(zip(settings['tool_selections'], settings['retained_tool_sources']))
                else:
                    pairs = [(settings['input_selection'], settings['retained_source'])]
                data, records, _, member, members = loaded[archive]
                for selection, expected in pairs:
                    actual = decode_retained_mesh_source(data, records, expected['mesh_object_id'],
                                                         selection, member, members)
                    assert actual == expected, (archive, 'old selected-source dictionary changed')
                    report['legacy_selected_source_controls'].append(dict(archive=archive,
                        mesh_object_id=expected['mesh_object_id'], evidence_report=name,
                        evidence_report_sha256=hashlib.sha256((root/name).read_bytes()).hexdigest(),
                        complete_dictionary_exact=True))

    data, records, features, member, members = loaded['meshremoves-8b2188cd274d/two_remove_first.f3d']
    definitions = decode_base_mesh_feature_definitions(data, records, features)
    meshes = decode_mesh_contents_variants(data, records, member, members)
    changed = copy.deepcopy(definitions)
    changed['partial'][0]['stored_mesh_object_ids'] = [0]
    failed = decode_base_mesh_sources(data, records, features, member, members,
                                      definitions=changed, mesh_contents=meshes)
    assert not failed['partial'] and failed['unresolved']
    report['guards'].append(dict(label='Stale or forged definition summary', reasons=failed['unresolved']))
    changed = copy.deepcopy(meshes)
    changed['decoded'][0]['asset_fusion_uuid'] = '00000000-0000-0000-0000-000000000000'
    failed = decode_base_mesh_sources(data, records, features, member, members,
                                      definitions=definitions, mesh_contents=changed)
    assert not failed['partial'] and failed['unresolved']
    report['guards'].append(dict(label='Stale or forged current mesh summary', reasons=failed['unresolved']))

    def rejects(label, call, expected=None):
        try:
            call()
        except ValueError as error:
            if expected is not None:
                assert str(error) == expected, (label, str(error))
            report['guards'].append(dict(label=label, reason=str(error)))
        else:
            raise AssertionError(label+' unexpectedly accepted')

    mesh = next(r for r in records if r.is_primary and r.object_id == 213)
    rejects('Duplicated primary mesh identity', lambda: decode_retained_mesh_record(
        data, records+[mesh], 213, member, members))
    changed_data = bytearray(data)
    changed_data[mesh.body+490:mesh.body+498] = (251).to_bytes(8, 'little')
    rejects('Mesh backlink names a different typed BaseMesh feature', lambda: decode_retained_mesh_record(
        bytes(changed_data), records, 213, member, members))
    owner = next(r for r in records if not r.is_primary and r.object_id == 202
                 and r.class_guid == 'A7AEA631-985B-4DD1-8CE2-DE2C-14B54081')
    changed_data = bytearray(data)
    changed_data[owner.body+6:owner.body+14] = (213).to_bytes(8, 'little')
    rejects('Retained route refuses a current counted member', lambda: decode_retained_mesh_record(
        bytes(changed_data), records, 213, member, members),
        'Retained source is actually in current counted members')
    selection = json.loads((root/'mesh-remove-decoding.json').read_text())['samples'][0]['expected_decoded']['decoded'][0]['settings']['input_selection']
    changed_selection = copy.deepcopy(selection)
    changed_selection['mesh_object_id'] = 0
    rejects('Old wrapper still rejects mismatched selected source before mesh parsing', lambda: decode_retained_mesh_source(
        data, records, 213, changed_selection, member, members),
        'Retained source selection does not match independently validated native mesh route')

    # Independent API evidence prevents using a nearby empty BaseFeature as a
    # fabricated parent of its separately serialized native BaseMesh records.
    for folder in ('meshremoves-8b2188cd274d', 'meshconverts-4b42d39fb1d5'):
        truth_path = root/folder/'ground_truth.json'
        truth = json.loads(truth_path.read_text())
        sample = truth['samples'][0]
        base = sample['base_after_edit']
        assert base['mesh_bodies'] == [] and base['brep_source_bodies'] == [] and base['brep_bodies'] == []
        source = (sample['imports'][0]['actual_meshes_during_edit'][0] if 'imports' in sample
                  else sample['source_during_edit'])
        assert source['baseOrFormFeature'] is None
        report['API_counterexamples'].append(dict(archive=folder+'/'+sample['file'],
            ground_truth_sha256=hashlib.sha256(truth_path.read_bytes()).hexdigest(),
            actual_BaseFeature_name=base['name'], actual_BaseFeature_mesh_bodies=base['mesh_bodies'],
            actual_BaseFeature_BRep_source_bodies=base['brep_source_bodies'],
            actual_BaseFeature_BRep_bodies=base['brep_bodies'],
            actual_imported_mesh_baseOrFormFeature=source['baseOrFormFeature'],
            conclusion='Owned setup is not a serialized parent relationship; no BaseFeature204 assignment made'))
    report['summary'] = dict(saved_files=len(report['samples']),
        partial_source_rows=sum(len(s['expected_decoded']['partial']) for s in report['samples']),
        retained_source_rows=sum(r['relationship_kind'] == 'RetainedStoredMeshRoute' for s in report['samples'] for r in s['expected_decoded']['partial']),
        current_source_rows=sum(r['relationship_kind'] == 'CurrentAcceptedMeshRoute' for s in report['samples'] for r in s['expected_decoded']['partial']),
        old_selected_source_full_dictionary_controls=len(report['legacy_selected_source_controls']),
        guards=len(report['guards']), old_mesh_summaries_exact=len(report['samples']),
        old_mesh_warning_clearances=0, feature_reclassifications=0)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--zstd-library', required=True)
    parser.add_argument('--prior-cache', type=Path, default=Path('/private/tmp/fusion-history-geometry-current.json'))
    parser.add_argument('--output', type=Path, default=ROOT/'base-mesh-source-decoding.json')
    args = parser.parse_args()
    report = validate(args.root.resolve(), args.zstd_library, args.prior_cache)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    print(json.dumps(report['summary']))

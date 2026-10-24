"""Focused stdlib validation of the completed actual Rule surface witness trace.

Reads saved files and SDK source text only; does not import adsk or decode ASM.
"""
import argparse
import ast
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CAPTURE = 'rulefilletsurfaces-7b26b40f98f7'
GENERATOR_SHA256 = '848bc2487eab060005b1b0c7fe349fa854c30e6da03dad2051f6cc20999eb984'
CASES = ('offsets_one_two', 'offsets_one_three')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate():
    folder = ROOT / CAPTURE
    truth = json.loads((folder/'ground_truth.json').read_text())
    events = [json.loads(line) for line in (folder/'journal.jsonl').read_text().splitlines() if line]
    source_path = folder/'executed-generator-source.txt'
    source = source_path.read_text()
    checks = []

    def check(label, value):
        if not value:
            raise AssertionError(label)
        checks.append(label)

    def nonnegative_int(value):
        return type(value) is int and value >= 0

    def zero(value):
        return type(value) in (int, float) and math.isfinite(value) and value == 0.

    check('exact executed generator snapshot and recorded SHA256',
        sha(source_path) == truth['executed_generator_sha256'] == GENERATOR_SHA256)
    check('two actual samples, no errors, bounded eight witnesses per case',
        truth['planned_cases'] == list(CASES) and len(truth['samples']) == 2
        and truth['errors'] == [] and truth['maximum_witnesses_per_case'] == 8)
    check('complete marker, final progress and journal agree',
        (folder/'complete.txt').read_text() == 'Complete; inspect actual truth and journal.\n'
        and events[-1]['phase'] == 'batch_complete' and events[-1]['sample_count'] == 2
        and events[-1]['error_count'] == 0
        and json.loads((folder/'progress.json').read_text()) == events[-1]
        and not (folder/'halted.txt').exists())
    check('all actual journal errors zero and UTC timestamps monotonic',
        all(e['error_count'] == 0 for e in events)
        and all(datetime.fromisoformat(a['time_utc']) <= datetime.fromisoformat(b['time_utc'])
            for a, b in zip(events, events[1:])))

    sdk_rows, snapshot_parts = [], []
    modules = {}
    for filename, expected in truth['sdk_runtime_sha256'].items():
        path = Path(filename)
        check('executed SDK runtime file SHA256 '+path.name, path.is_file() and sha(path) == expected)
        modules[path.stem] = path.read_text()
        sdk_rows.append(dict(path=filename, sha256=expected))
    check('exact recorded core and fusion SDK modules', set(modules) == {'core', 'fusion'})
    names_by_module = (
        ('core', ('Base', 'ObjectCollection', 'ValueInput', 'SurfaceEvaluator', 'NurbsSurface', 'Point3DVector')),
        ('fusion', ('BRepBody', 'BRepFace', 'BRepConvertOptions', 'FilletFeatures', 'RuleFilletFeatureInput',
            'Design', 'Timeline', 'TimelineObject', 'OffsetFeatures', 'OffsetFeatureInput', 'OffsetFeature')))
    for module, names in names_by_module:
        for name in names:
            text = modules[module]
            start = text.index('class '+name+'(')
            end = text.find('\nclass ', start+1)
            snapshot_parts.append(text[start:] if end < 0 else text[start:end])
    snapshot = '\n'.join(snapshot_parts).encode()
    check('executed SDK surface snapshot replay and SHA256',
        snapshot == (folder/'executed-sdk-surface.txt').read_bytes()
        and hashlib.sha256(snapshot).hexdigest() == truth['executed_sdk_surface_sha256'])
    enum = next(node for node in ast.parse(modules['fusion']).body
        if isinstance(node, ast.ClassDef) and node.name == 'FeatureOperations')
    enum_value = next(node.value for node in enum.body
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name)
            and target.id == 'NewBodyFeatureOperation' for target in node.targets))
    operation = 3  # Literal actual readback, not a Python SDK constant evaluation.
    check('NewBody enum delegates to the concrete native SDK symbol',
        isinstance(enum_value, ast.Attribute) and isinstance(enum_value.value, ast.Name)
        and enum_value.value.id == '_fusion'
        and enum_value.attr == 'FeatureOperations_NewBodyFeatureOperation'
        and 'adsk.fusion.FeatureOperations.NewBodyFeatureOperation, False)' in source)
    check('executed source uses concrete equality and rejects nonboolean results',
        'comparison = type(left).__eq__(left, right)' in source
        and 'if comparison is NotImplemented:' in source and 'if type(comparison) is not bool:' in source
        and 'return bool(adsk.core.Base.__eq__' not in source
        and '_fusion.BRepFace___eq__' in modules['fusion']
        and '_fusion.OffsetFeature___eq__' in modules['fusion'])

    # These exact statements are in the hash-pinned executed source, linking
    # journal release markers to completed GC calls. The journal cannot observe
    # every C++ destructor or prove future crash absence.
    ordered_statements = (
        "witness = create_witness(", "witness['create_frame_gc_collected'] = gc.collect()",
        "journal('witness_create_wrappers_released'", "witness['rolled_input'] = read_rolled_witness(",
        "witness['rolled_getter_frame_gc_collected_before_restore'] = gc.collect()",
        "journal('witness_rolled_wrappers_released_before_restore'",
        "witness['restoration'] = restore_after_witness(doc)",
        "witness['restoration_frame_gc_collected'] = gc.collect()", "journal('witness_restored'",
        "sample['witness_finalize_frame_gc_collected'] = gc.collect()",
        "journal('witness_export_complete'", "sample['close_owned_document_returned'] = bool(doc.close(False))",
        "journal('owned_document_closed'")
    positions = [source.index(statement) for statement in ordered_statements]
    check('executed source GC and restoration/close ordering', positions == sorted(positions))

    samples, archives = [], []
    for case, sample in zip(CASES, truth['samples']):
        check(case+' actual source feature healthy and getter errors empty',
            sample['file'] == case+'.f3d' and sample['feature_health_state'] == 0
            and sample['feature_warning'] == '' and sample['getter_errors'] == [])
        check(case+' exactly eight witness readbacks and no ASM identity claim',
            len(sample['witnesses']) == sample['total_deep_face_count'] == 8
            and all(w['native_recipe_binding'] is None for w in sample['witnesses']))
        check(case+' actual original/finalizer GC counters and owned close',
            all(nonnegative_int(sample[key]) for key in ('populate_frame_gc_collected',
                'finalize_frame_gc_collected', 'witness_finalize_frame_gc_collected'))
            and sample['close_owned_document_returned'] is True
            and sample['pre_witness_archive_hash_unchanged'] is True)
        archive_rows = []
        for filename, expected_hash, size in ((sample['file'], sample['archive_sha256'], sample['archive_size_bytes']),
                (sample['witness_archive']['file'], sample['witness_archive']['sha256'], sample['witness_archive']['size_bytes'])):
            path = folder/filename
            check(case+' actual export hash/size '+filename, path.is_file() and path.stat().st_size == size
                and size > 0 and sha(path) == expected_hash)
            archive_rows.append(dict(file=CAPTURE+'/'+filename, sha256=expected_hash, size_bytes=size))
        check(case+' separate witness export count/file', sample['witness_archive']['file'] == case+'_witnesses.f3d'
            and sample['witness_archive']['witness_count'] == 8)
        trace = [e for e in events if e['case'] == case]
        expected_phases = ['creating_owned_document', 'creating_feature', 'converting_temporary_body',
            'wrappers_released_before_export', 'pre_witness_export_complete']
        for ordinal in range(8):
            expected_phases += ['creating_face_witness', 'witness_create_wrappers_released',
                'witness_rolled_wrappers_released_before_restore', 'witness_restored']
        expected_phases += ['witness_export_complete', 'owned_document_closed']
        check(case+' complete exact lifecycle journal order', [e['phase'] for e in trace] == expected_phases)
        check(case+' original export journal hash agrees', trace[4]['file'] == sample['file']
            and trace[4]['sha256'] == sample['archive_sha256'])
        witnesses = []
        for ordinal, witness in enumerate(sample['witnesses']):
            label = case+' witness'+str(ordinal)
            check(label+' actual singleton same-document BRepFace equality',
                witness['source_token_resolution_count'] == witness['input_entities_count'] == 1
                and witness['input_entity_object_type'] == 'adsk::fusion::BRepFace'
                and witness['input_entity_equals_resolved_source'] is True)
            check(label+' actual input and feature controls healthy zero-offset NewBody',
                witness['actual_input_chain_selection'] is False and witness['actual_chain_selection'] is False
                and witness['actual_input_operation'] == witness['actual_operation'] == operation
                and zero(witness['actual_input_distance_cm']) and zero(witness['actual_distance_cm'])
                and witness['feature_health_state'] == 0 and witness['feature_warning'] == ''
                and witness['feature_object_type'] == 'adsk::fusion::OffsetFeature')
            rolled = witness['rolled_input']
            restoration = witness['restoration']
            check(label+' actual pre-node singleton equality and restoration',
                rolled['rolled_before_node'] is True and rolled['entities_count'] == 1
                and rolled['entity_object_type'] == 'adsk::fusion::BRepFace'
                and rolled['entity_equals_resolved_source'] is True
                and restoration['moved_to_end'] is True and restoration['compute_completed'] is True)
            check(label+' actual GC counts and journal ordinal',
                all(nonnegative_int(witness[key]) for key in ('create_frame_gc_collected',
                    'rolled_getter_frame_gc_collected_before_restore', 'restoration_frame_gc_collected'))
                and all(e['witness_ordinal'] == ordinal for e in trace[5+ordinal*4:9+ordinal*4]))
            witnesses.append(dict(ordinal=ordinal, feature_metadata_name=witness['name'],
                input_singleton_BRepFace_equality=True, rolled_singleton_BRepFace_equality=True,
                OffsetFeature_metadata_lookup_equality_verified_by_executed_source_gate=True,
                zero_offset_NewBody=True, feature_healthy=True, rolled_before_node=True,
                restoration_completed=True, native_ASM_binding=None))
        archives.extend(archive_rows)
        samples.append(dict(case=case, archives=archive_rows, actual_witnesses=witnesses,
            healthy_owned_close=True, original_archive_hash_unchanged=True,
            lifecycle_phases=[e['phase'] for e in trace]))
    check('four actual exported archives and two owned cases', len(archives) == 4 and len(samples) == 2)
    check('next owned case starts only after prior owned close',
        next(i for i,e in enumerate(events) if e['case'] == CASES[0] and e['phase'] == 'owned_document_closed')
        < next(i for i,e in enumerate(events) if e['case'] == CASES[1] and e['phase'] == 'creating_owned_document'))
    return dict(status='Saved actual trace validation passed', capture=CAPTURE,
        scope='Two healthy owned Rule surface captures and sixteen actual singleton Offset API witness readbacks; native ASM face/VBL binding UNPROVEN',
        evidence_sha256={name: sha(folder/name) for name in ('ground_truth.json', 'journal.jsonl',
            'progress.json', 'complete.txt', 'executed-generator-source.txt', 'executed-sdk-surface.txt')},
        source_sha256={Path(__file__).name: sha(Path(__file__))}, sdk_runtime=sdk_rows,
        actual_NewBody_operation_readback=operation,
        operation_scope='Literal actual integer 3 from create/readback using the named native SDK NewBody enum; no SDK binary imported',
        samples=samples, checks=checks,
        external_observations=dict(provenance='Parent-provided external process/CER command observations; not executed by this validator',
            Fusion_process_PID=5619, process_alive_after_capture_reported=True,
            no_newer_CER_than_reported_local_time='2026-10-21 15:45:56',
            command_output_independently_verified_by_validator=False),
        limitations=['API native equality does not assign an ASM face by token, temporary ID, enumeration order or coordinates.',
            'GC ordering is source-pinned and journal-correlated; individual C++ destructor completion and future crash absence are not proved.',
            'OffsetFeature identity succeeds through the executed concrete equality/name-lookup gate; a separate raw equality return is not stored.',
            'No native parser, reader main pipeline, adsk import or live API call is performed.'],
        validation=dict(healthy_owned_captures=2, witnesses=16, actual_exports=4,
            healthy_owned_closes=2, focused_checks=len(checks), live_API_calls=0, main_reader_calls=0))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT/'rule-surface-witness-native-validation.json')
    args = parser.parse_args()
    report = validate()
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    print(json.dumps(report['validation'], sort_keys=True))

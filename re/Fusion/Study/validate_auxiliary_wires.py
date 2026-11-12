"""Focused shell-owned auxiliary line-wire proof and solid-graph preservation."""

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

from asm_records import inspect_asm
from decode_basics import decode_basics
from decode_body_asm_identifiers import decode_body_asm_identifiers
from decode_brep import decode_topology
from fusion_archive import read_members
from fusion_metadata import design_records
from validate_body_asm_identifiers import _raw_mapping_frame

FILES = ['splitfacemodes-4fc4adf2a868/along_vector.f3d',
         'splitfacemodes-4fc4adf2a868/closest_point.f3d']


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def near(a, b):
    return len(a) == len(b) and all(math.isclose(x, y, abs_tol=1e-9, rel_tol=1e-9) for x, y in zip(a, b))


def previous_analytic_schema(graphs):
    """Compare historical graph snapshots across the documented field correction.

    This does not tolerate geometry differences: the old conflated parameter
    scale must still equal physical radius within numeric precision here.
    """
    result = copy.deepcopy(graphs)
    for graph in result:
        for surface in graph['analytic_surfaces']:
            geometry = surface['geometry']
            if geometry and geometry['kind'] in ('Cone', 'Cylinder') and 'stored_u_parameter_scale' in geometry:
                scale = geometry.pop('stored_u_parameter_scale')
                assert math.isclose(geometry['raw_radius'], scale, abs_tol=1e-9, rel_tol=1e-9)
                geometry['raw_radius'] = scale
                geometry['is_v_reversed'] = geometry.pop('is_u_reversed')
    return result


def validate(zstd_library, baseline):
    root = Path(__file__).resolve().parent
    truth = json.loads((root / 'splitfacemodes-4fc4adf2a868/ground_truth.json').read_text())
    report = {'scope': 'Observed initial ASM shell-owned single-line WIRE topology; unnumbered auxiliary BODY identity remains unresolved',
              'integration': {
                  'parser': 'decode_brep.decode_topology(parsed)',
                  'shared_hook_changes': 'None; existing native BODY stored-ID reader now accepts the decoded auxiliary BODY graph',
                  'new_graph_fields': ['counts.wire', 'wire_indices', 'wire_coedge_rings', 'topology_kind', 'wire_scope'],
                  'compatibility': 'Wire-specific fields are emitted only for the observed wire variant; prior topology/geometry is preserved across the documented analytic parameter-scale/reversal-field correction',
                  'validation_command': '/usr/bin/python3 validate_auxiliary_wires.py',
              }, 'native_layout': {
                  'wire': 'Observed8tokens: attribute pointer,storedID,pattern pointer,nextWire,firstCoedge,shell,uninterpreted pointer6,boolean flag7. Shell.firstWire and wire.shell reciprocate; pointer6 null and flag7false required.',
                  'coedge_owner': 'Field8 is typed LOOP for face loops or typed WIRE for this observed shell-owned wire. Wire coedge self-next/self-previous, partner/pcurve null.',
                  'body_chain': 'BODY2 ->lump5 ->shell8 ->wire10 ->coedge15 ->edge21 ->vertices32/33 ->points57/58, with each supported owner link reciprocal',
                  'line': 'edge21 references decoded straightcurve34. Distinct endpoint vertex identities form an open line despite the circular coedge traversal container.',
              }, 'samples': [], 'solid_topology_preservation': [], 'guards': [], 'limitations': [
                  'Only a standalone one-lump/one-shell/one-wire/single-straight-edge variant is supported.',
                  'Direct BODY-owned wires, mixed face/wire shells, multiple wires, general polylines, closed wires and other curve kinds remain unsupported.',
                  'Opaque wire pointer6 and flag7 are preserved without assigning additional meaning; unobserved populated/true variants are rejected.',
                  'BODY storedID=-1 remains unassociated; source SketchLine equality is geometric corroboration, not persistent native source identity.',
                  'Current visibility, final body lifecycle, coordinate solving and regeneration remain unresolved.',
              ]}
    contexts = {}
    for relative in FILES:
        path = root / relative
        members = read_members(path, zstd_library)
        member = next(m for m in members if m.endswith('FusionDesignSegmentType1/BulkStream.dat'))
        data = members[member]
        records, _ = design_records(data, members[member.replace('BulkStream.dat', 'MetaStream.dat')])
        mapping = _raw_mapping_frame(data, records, member, 8)
        blob = mapping['history_blob_member']
        parsed = inspect_asm(members[blob])
        topology = decode_topology(parsed)
        assert not topology['unresolved']
        nodes = {n['index']: n for n in topology['nodes']}
        graphs = {g['body_index']: g for g in topology['body_graphs']}
        assert set(graphs) == {1, 2}
        native = decode_body_asm_identifiers(data, records, member, members, {'decoded': [mapping]})
        assert not native['unresolved'] and len(native['decoded']) == 1
        patch, = native['decoded'][0]['bindings']
        assert (patch['native_body_object_id'], patch['stored_handle'], patch['asm_body_index']) == (275, 1, 1)
        auxiliary, = native['decoded'][0]['auxiliary_declared_roots']
        assert auxiliary['asm_record_index'] == 2 and auxiliary['stored_entity_id'] == -1
        assert 'native_body_object_id' not in auxiliary
        wire_graph = graphs[2]
        assert wire_graph['counts'] == {'lump': 1, 'shell': 1, 'face': 0, 'loop': 0,
                                        'coedge': 1, 'edge': 1, 'vertex': 2, 'wire': 1}
        ring, = wire_graph['wire_coedge_rings']
        assert ring['wire_index'] == 10 and ring['edge_indices'] == [21]
        assert nodes[15]['wire_index'] == 10 and nodes[15]['loop_index'] is None
        actual = next(s for s in truth['samples'] if s['file'] == path.name)
        api_line, = actual['splitting_tools']
        actual_points = [api_line['start_cm'], api_line['end_cm']]
        raw_points = wire_graph['raw_vertex_positions']
        assert all(near(p, q) for p, q in zip(sorted(actual_points), sorted(raw_points)))
        edge, curve = nodes[21], nodes[34]
        evaluated = [[o + t * d for o, d in zip(curve['raw_origin'], curve['direction'])]
                     for t in [edge['start_parameter'], edge['end_parameter']]]
        assert all(near(p, q) for p, q in zip(sorted(actual_points), sorted(evaluated)))
        assert graphs[1]['counts']['face'] == actual['result']['face_count'] == 7
        model = decode_basics(path, zstd_library)
        stream = next(s for s in model['streams'] if s['member'] == member)
        prop = next(b for b in stream['body_properties']['bodies'] if b['object_id'] == patch['native_body_object_id'])
        assert prop['name'] == actual['faces_to_split'][0]['body_name']
        assert stream['body_asm_identifiers']['unresolved'] == []
        assert actual['result']['body_count'] == len(native['decoded'][0]['bindings']) == 1
        report['samples'].append({'file': relative, 'history_blob_member': blob,
                                  'native_body_associations': native,
                                  'wire_body_graph': wire_graph,
                                  'wire_and_coedge_nodes': [nodes[10], nodes[15]],
                                  'API_checks': {'mapped_native_body_name_matches_actual_API': True,
                                                 'mapped_solid_face_count_matches_actual_API': True,
                                                 'mapped_body_count_matches_actual_API_result_count': True,
                                                 'auxiliary_wire_endpoint_and_curve_cache_match_API_tool_line': True},
                                  'actual_API_tool_line': api_line, 'raw_wire_endpoint_points_cm': raw_points,
                                  'curve_parameter_endpoint_points_cm': evaluated,
                                  'persistent_source_identity': 'Unresolved; no native SketchLine-to-auxiliary-BODY link inferred from matching coordinates'})
        contexts[relative] = data, records, member, members, mapping, parsed
    for old in baseline:
        members = read_members(root / old['file'], zstd_library)
        topology = decode_topology(inspect_asm(members[old['member']]))
        previous = [g for g in topology['body_graphs'] if g['body_index'] in old['body_graph_indices']]
        current_hash = digest(previous)
        assert [g['body_index'] for g in previous] == old['body_graph_indices']
        comparison_hash = current_hash
        if current_hash != old['body_graphs_sha256']:
            comparison_hash = digest(previous_analytic_schema(previous))
        assert comparison_hash == old['body_graphs_sha256'], (old['file'], old['member'])
        report['solid_topology_preservation'].append({
            'file': old['file'], 'member': old['member'], 'body_graph_indices': old['body_graph_indices'],
            'body_graphs_sha256': old['body_graphs_sha256'], 'current_body_graphs_sha256': current_hash,
            'comparison_body_graphs_sha256': comparison_hash,
            'complete_prior_graph_outputs_exact': current_hash == old['body_graphs_sha256'],
            'preserved_after_documented_analytic_field_correction': True})

    context = contexts[FILES[0]]
    data, records, member, members, mapping, parsed = context
    blob = mapping['history_blob_member']

    def rejected(label, changed):
        mutated = {**members, blob: bytes(changed)}
        bad_topology = decode_topology(inspect_asm(mutated[blob]))
        assert 1 in {g['body_index'] for g in bad_topology['body_graphs']}
        assert 2 not in {g['body_index'] for g in bad_topology['body_graphs']}
        result = decode_body_asm_identifiers(data, records, member, mutated, {'decoded': [mapping]})
        assert not result['decoded'] and len(result['unresolved']) == 1
        report['guards'].append({'guard': label, 'rejected': True,
                                 'solid_body_graph_preserved': True,
                                 'topology_diagnostics': bad_topology['unresolved'],
                                 'native_mapping_rejection': result['unresolved'][0]['reason']})

    for record_index, field_index, wrong_target, label in [
        (10, 5, 7, 'Wire shell reference must reciprocate the containing auxiliary shell'),
        (15, 8, 17, 'Wire coedge container must be the explicit WIRE, not another typed entity'),
        (21, 7, 16, 'Wire edge must point back to its own coedge'),
        (32, 3, 22, 'Wire endpoint vertex must point back to its edge'),
    ]:
        changed = bytearray(members[blob])
        struct.pack_into('<q', changed, parsed['records'][record_index]['tokens'][field_index]['offset'] + 1, wrong_target)
        rejected(label, changed)
    changed = bytearray(members[blob])
    history = next(r for r in parsed['records'] if r['section'] == 'history')
    struct.pack_into('<q', changed, parsed['records'][10]['tokens'][4]['offset'] + 1, history['index'])
    rejected('Wire first-coedge reference cannot leave the initial geometry table', changed)
    changed = bytearray(members[blob])
    changed[parsed['records'][10]['tokens'][7]['offset']] = 10
    rejected('Unobserved true wire flag7 variant remains unsupported', changed)
    report['summary'] = {'wire_files': len(report['samples']),
                         'new_auxiliary_wire_body_graphs': len(report['samples']),
                         'native_mappings_recovered': len(report['samples']),
                         'unassociated_BODY_minus_one_roots_retained': len(report['samples']),
                         'actual_API_line_geometry_controls': len(report['samples']),
                         'prior_body_graphs_preserved_after_analytic_field_correction': sum(len(b['body_graph_indices']) for b in baseline),
                         'prior_complete_body_graphs_preserved_exact': sum(len(b['body_graph_indices']) for b in report['solid_topology_preservation'] if b['complete_prior_graph_outputs_exact']),
                         'prior_control_streams': len(baseline), 'malformed_guards': len(report['guards'])}
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zstd-library')
    parser.add_argument('--baseline', help='Pre-change focused topology snapshot; otherwise reuse report baseline hashes')
    parser.add_argument('--output', default='auxiliary-wire-decoding.json')
    args = parser.parse_args()
    zstd = args.zstd_library or next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib'))
    baseline = json.loads(Path(args.baseline).read_text()) if args.baseline else json.loads(
        Path(__file__).with_name('auxiliary-wire-decoding.json').read_text())['solid_topology_preservation']
    report = validate(zstd, baseline)
    Path(args.output).write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report['summary'], sort_keys=True))

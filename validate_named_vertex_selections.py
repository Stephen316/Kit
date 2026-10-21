"""Saved named-VERTEX feasibility evidence; no speculative runtime resolver."""

import argparse
from collections import Counter
import copy
import json
from pathlib import Path
import struct

from asm_records import inspect_asm
from decode_asm_recipe_tags import decode_asm_generic_tags
from decode_basics import decode_basics
from decode_brep import decode_topology
from decode_brep_recipes import RECIPE_GUID
from decode_counted_asm_names import decode_counted_asm_name
from decode_recipe_components import decode_counted_recipe
from fusion_archive import read_members
from fusion_metadata import design_records

ROOT = Path(__file__).resolve().parent
NAMED_FILES = ('splinepatches-900d152c2380/splinepatches.f3d', 'splinepatches-ac5e846e59c0/splinepatches.f3d')


def key(terms):
    return tuple((t['name'], t['stored_index'], tuple(t['stored_reference_components_int32'])) for t in terms)


def validate(zstd_library):
    report = {'scope': 'Historical559-file baseline feasibility before namedvertexprobe-8d81619f74e6; original inventory remains unchanged. Followup actual probe evidence is in named-vertex-selection-decoding.json',
        'inventory_provenance': {'source': 'Two bounded read-only censuses over the559-file fusion-class-catalog.json; initial ASM generic VERTEX owners and primary native vertex_recipe_data records, no whole-main audit',
            'initial_named_vertex_attributes': 48, 'named_vertex_archives': list(NAMED_FILES),
            'primary_vertex_recipes': 78, 'vertex_recipe_archives': 34,
            'followup': 'Validator independently rechecks all48 VERTEX payload/owner/topology routes and the fixed78-recipe native inventory. It does not repeat whole-corpus discovery.'},
        'native_recipe_inventory': [], 'named_vertices': [], 'body_API_context_controls': [], 'guards': [],
        'capture_proposal': {'generator': 'GenerateNamedVertexSelectionProbe.py',
            'source_archive': NAMED_FILES[0], 'cases': ['construction_polynomial_vertex0', 'scale_rational_vertex2'],
            'API_feasibility': ['Installed SDK ConstructionPointInput.setByPoint explicitly permits BRepVertex in parametric modeling; PointDefinition.pointEntity returns actual source.',
                'Installed SDK ScaleFeatures.createInput accepts BRepVertex reference point; actual Scale.point/inputEntities require rollback immediately before feature.'],
            'ownership': 'Fresh new archive import per case; modify/export/close only owned imported document, restore timeline end before export/close.',
            'requested_vs_actual': 'Collection indices construct the capture; actual source types/tokens/tempIds/geometry are independently read. No requested index becomes native recipe identity.',
            'success_criterion': 'New native recipe selects complete explicit VERTEX naming group through typed descriptor/body mapping; preserve unresolved result if API export uses other recipe semantics.'},
        'limitations': ['Original559-file baseline native recipe files and explicit VERTEX files are disjoint; that baseline alone cannot qualify direct selection semantics. Two later actual probe archives are validated separately.',
            'All saved vertex payloads begin signed integer-1. Only existing40-byte three-face layout has independently decoded operand semantics;64/84-byte layouts remain opaque here.',
            'Complete naming groups and reciprocal VERTEX/point/edge/BODY relationships establish cache provenance only, not native selected source or persistent topology identity.',
            'History .smbh roots map through explicit native stored handles; parallel .smb roots are not associated by order, coordinates or matching names.',
            'Existing Pipe/Scale/ConstructionPoint three-face incidence resolver remains the runtime path for supported actual selections; it is not duplicated.',
            'API source/body counts corroborate named fixture context, not an attribute-to-selected-vertex identity. No live probe results or native writer are claimed by this report.']}
    contexts = {}
    def load(relative):
        if relative not in contexts: contexts[relative] = read_members(ROOT/relative, zstd_library)
        return contexts[relative]
    for relative, ids in RECIPE_TARGETS.items():
        members = load(relative); found = []
        for member, data in members.items():
            if not member.endswith('/BulkStream.dat'): continue
            records, _ = design_records(data, members[member.replace('BulkStream.dat', 'MetaStream.dat')])
            for record in records:
                if not record.is_primary or record.class_guid != RECIPE_GUID: continue
                recipe = decode_counted_recipe(data, record)
                if recipe['payload_kind'] != 'vertex_recipe_data': continue
                payload = bytes.fromhex(recipe['payload_hex']); leading = struct.unpack_from('<i', payload)[0]
                assert leading == -1
                found.append(record.object_id)
                report['native_recipe_inventory'].append({'file': relative, 'member': member, 'recipe_object_id': record.object_id,
                    'payload_size': len(payload), 'leading_int32': leading, 'name_table_size': len(recipe['name_table']),
                    'operation_status': 'Existing three-face incidence grammar' if len(payload) == 40 else 'Opaque alternate operation; leading field retained literally'})
        assert sorted(found) == ids
    assert len(report['native_recipe_inventory']) == 78
    native_files = set(RECIPE_TARGETS); assert native_files.isdisjoint(NAMED_FILES)
    all_counts = Counter(); guard_source = None; mapped = 0
    for relative in NAMED_FILES:
        members = load(relative); model = decode_basics(ROOT/relative, zstd_library); stream = model['streams'][0]
        joins = stream['body_asm_identifiers']; assert not joins['unresolved']
        properties = {b['object_id']: b for b in stream['body_properties']['bodies']}
        for member, data in members.items():
            if member.endswith('/BulkStream.dat'):
                records, _ = design_records(data, members[member.replace('BulkStream.dat', 'MetaStream.dat')])
                assert not any(r.is_primary and r.class_guid == RECIPE_GUID and decode_counted_recipe(data, r)['payload_kind'] == 'vertex_recipe_data' for r in records)
        api = json.loads((ROOT/Path(relative).parent/'ground_truth.json').read_text()); cases = {c['name']: c for c in api['cases']}
        for member, blob in members.items():
            if not member.endswith(('.smb', '.smbh')): continue
            parsed = inspect_asm(blob); assert parsed['complete_token_stream']
            names = decode_asm_generic_tags(blob, parsed, allow_fpm_tracking=True); assert not names['unresolved']
            topology = decode_topology(parsed); assert not topology['unresolved']
            nodes = {n['index']: n for n in topology['nodes']}; vertex_tags = [t for t in names['tags'] if t['owner_kind'] == 'vertex']
            term_groups = Counter(key(t['terms']) for t in vertex_tags)
            for tag in vertex_tags:
                index = tag['owner_record_index']; vertex = nodes[index]; assert vertex['kind'] == 'vertex'
                assert term_groups[key(tag['terms'])] == 1 and vertex['attribute_index'] == tag['owner_attribute_chain'][0]
                record = parsed['records'][tag['attribute_record_index']]
                payload = decode_counted_asm_name(record)
                assert bytes.fromhex(payload['payload_hex']) == blob[payload['payload_offset']:payload['payload_end_offset']]
                point = nodes[vertex['point_index']]; edge = nodes[vertex['first_edge_index']]
                assert point['kind'] == 'point' and edge['kind'] == 'edge' and index in (edge['start_vertex_index'], edge['end_vertex_index'])
                graphs = [g for g in topology['body_graphs'] if index in g['vertex_indices']]; graph, = graphs
                assert edge['index'] in graph['edge_indices']
                bindings = [(m, b) for m in joins['decoded'] if m['history_blob_member'] == member for b in m['bindings'] if b['asm_body_index'] == graph['body_index']]
                entry = {'file': relative, 'member': member, 'attribute_record_index': tag['attribute_record_index'],
                    'vertex_record_index': index, 'complete_terms': tag['terms'], 'owner_attribute_chain': tag['owner_attribute_chain'],
                    'point_record_index': point['index'], 'raw_point': point['raw_origin'], 'incident_first_edge_index': edge['index'],
                    'body_record_index': graph['body_index'], 'native_body_object_id': None,
                    'selected_source_status': 'Unresolved; no native vertex recipe in this archive'}
                if bindings:
                    mapping, binding = bindings[0]; assert len(bindings) == 1
                    assert parsed['records'][graph['body_index']]['tokens'][1]['value'] == binding['stored_handle'] == binding['asm_stored_entity_id']
                    body = properties[binding['native_body_object_id']]; case = cases[body['name']]
                    assert graph['counts']['vertex'] == case['vertex_count'] == 4 and graph['counts']['edge'] == case['edge_count'] == 4
                    entry.update(native_body_object_id=binding['native_body_object_id'], native_body_name=body['name'], mapping_object_id=mapping['mapping_record_object_id'], stored_body_handle=binding['stored_handle'])
                    mapped += 1
                report['named_vertices'].append(entry); all_counts[member.rsplit('.', 1)[-1]] += 1
                guard_source = blob, parsed, record
        report['body_API_context_controls'].append({'file': relative, 'saved_API_patch_cases': sorted(cases),
            'native_mapped_bodies': [b['native_body_object_id'] for m in joins['decoded'] for b in m['bindings']],
            'native_vertex_recipes_present': False})
    assert len(report['named_vertices']) == 48 and mapped == 24
    blob, parsed, record = guard_source
    def reject(label, alter):
        bad = copy.deepcopy(parsed); alter(bad)
        result = decode_asm_generic_tags(blob, bad, allow_fpm_tracking=True)
        assert any(r['attribute_record_index'] == record['index'] for r in result['unresolved'])
        assert not any(t['attribute_record_index'] == record['index'] for t in result['tags'])
        report['guards'].append({'case': label, 'rejected_by_production_reader': True})
    reject('Claimed VERTEX owner changed to different typed vertex', lambda p: p['records'][record['index']]['tokens'][4].update(value=next(r['index'] for r in p['records'] if r['name']=='vertex' and r['index'] != record['tokens'][4]['value'])))
    reject('Reciprocal previous-attribute link corrupted', lambda p: p['records'][record['index']]['tokens'][3].update(value=record['index']))
    reject('Unknown counted component count', lambda p: p['records'][record['index']]['tokens'][14].update(value=4))
    reject('Payload bytes differ from exact stored name', lambda p: p['records'][record['index']]['tokens'][12].update(value='9'*len(record['tokens'][12]['value'])))
    report['summary'] = {'named_vertex_cache_attributes': 48, 'named_vertex_archives': 2, 'native_mapped_history_vertices': mapped,
        'unassociated_parallel_asset_vertices': 24, 'native_vertex_recipes': 78, 'native_vertex_recipe_archives': 34,
        'direct_named_selection_positive_fixtures': 0, 'recipe_name_archive_overlap': [],
        'native_recipe_payload_sizes': dict(Counter(r['payload_size'] for r in report['native_recipe_inventory'])), 'guards': len(report['guards']),
        'runtime_decoder_added_in_original_baseline': False}
    return report


def validate_probe(zstd_library):
    import math
    from decode_named_vertex_selections import decode_named_vertex_selections, FEATURE_CLASSES
    from decode_selection_recipe_incidence import decode_selection_recipe_incidence
    directory = 'namedvertexprobe-8d81619f74e6'
    truth = json.loads((ROOT/directory/'ground_truth.json').read_text())
    assert truth['status'] == 'complete' and not truth['errors']
    report = {'scope': 'Two actual post-baseline direct named-VERTEX captures; explicit typed identity routes precede geometry checks',
        'interface': 'decode_named_vertex_selections(data,records,features,member,members,body_identifier_summary,body_selections=None,*,descriptor_ids=None)',
        'integration': 'Late independent named_vertex_selections summary and owner-feature attachments. Do not replace old selection_context_recipes/selection_recipe_incidence failures or promote full recipe/modeling semantics.',
        'historical_feasibility_report': 'named-vertex-selection-feasibility.json retains original559-file baseline; these two new archives are separate evidence',
        'cases': [], 'guards': [], 'old_controls': [],
        'limitations': ['Only observed96-byte direct-name-table0 operation prefix is supported; nonzero direct-name positions and other operation forms remain unsupported.',
            'Last six int32 fields remain literal opaque procedure data, not decoded parameters/IDs.',
            'Selected direct VERTEX and both named incident EDGEs must match complete groups uniquely in the explicitly mapped BODY; coordinates never choose candidates.',
            'Scale auxiliary FACE group has no stored match. Its absence is retained explicitly rather than inventing a historical FACE or claiming complete recipe evaluation.',
            'Point coordinate agreement is checked after identity association; no persistent topology, source-history reconstruction, world placement or current/final visibility claim.']}
    contexts = []
    for sample in truth['samples']:
        assert sample['status'] == 'exported' and not sample['getter_errors'] and sample['close_owned_document_result'] is True
        relative = directory+'/'+sample['file']; members=read_members(ROOT/relative,zstd_library)
        model=decode_basics(ROOT/relative,zstd_library);stream=model['streams'][0];member=stream['member'];data=members[member]
        records,_=design_records(data,members[member.replace('BulkStream.dat','MetaStream.dat')]);primary={r.object_id:r for r in records if r.is_primary}
        features=stream['features'];before=copy.deepcopy(features)
        result=decode_named_vertex_selections(data,records,features,member,members,stream['body_asm_identifiers'])
        assert features == before and not result['unresolved'] and len(result['associations']) == 1
        association,=result['associations'];descriptor_id=association['descriptor_object_id']
        owner=primary[association['descriptor_owner_feature_object_id']]
        assert owner.class_guid == FEATURE_CLASSES[association['feature_kind']]
        actual=sample['actual']['source_vertex'];requested=sample['selected_vertex_before_feature']
        assert actual['entity_type'] == requested['entity_type'] == 'adsk::fusion::BRepVertex'
        error=math.dist(association['cached_raw_point'], actual['world_point_cm'])
        assert error < 1e-10 and math.dist(association['cached_raw_point'],requested['world_point_cm']) < 1e-10
        assert association['point_context_agrees_after_identity_join']
        assert association['operation_evidence']['payload_hex'] == decode_counted_recipe(data,primary[association['recipe_object_id']])['payload_hex']
        if association['feature_kind'] == 'Scale':
            assert sample['actual']['scale_factor'] == 1.25 and sample['actual']['is_uniform']
            assert association['auxiliary_face_name_evidence']['candidate_count'] == 0
        else:
            assert association['auxiliary_face_name_evidence']['candidate_count'] == 1
        old=decode_selection_recipe_incidence(data,records,features,member,members,stream['body_asm_identifiers'],descriptor_ids=[descriptor_id])
        assert not old['associations'] and len(old['unresolved']) == 1
        report['cases'].append({'file':relative, 'expected_summary':result,
            'actual_API_selected_type':actual['entity_type'], 'actual_API_body_name':actual['body']['name'],
            'actual_API_selected_point_cm':actual['world_point_cm'], 'coordinate_error_after_typed_identity_join':error,
            'actual_API_feature_type':sample['actual']['feature_type'],
            'original_incidence_warning_retained':old['unresolved'], 'feature_dictionaries_unchanged':True})
        contexts.append((data,records,features,member,members,stream,association))
    data,records,features,member,members,stream,association=contexts[0];primary={r.object_id:r for r in records if r.is_primary}
    descriptor=primary[association['descriptor_object_id']];recipe=primary[association['recipe_object_id']]
    decoded_recipe=decode_counted_recipe(data,recipe);payload=bytes.fromhex(decoded_recipe['payload_hex'])
    recipe_start=data.index(payload,recipe.body,recipe.end)
    def reject(label, altered_data=None, altered_members=None):
        result=decode_named_vertex_selections(altered_data if altered_data is not None else data,records,features,member,
            altered_members if altered_members is not None else members,stream['body_asm_identifiers'],descriptor_ids=[descriptor.object_id])
        assert not result['associations'] and len(result['unresolved']) == 1
        report['guards'].append({'case':label,'rejected':True,'reason':result['unresolved'][0]['reason']})
    bad=bytearray(data);struct.pack_into('<i',bad,recipe_start,1);reject('Uncaptured/nonzero direct name-table selector',bytes(bad))
    bad=bytearray(data);struct.pack_into('<i',bad,recipe_start+8,2);reject('Wrong fixed operation count/schema',bytes(bad))
    backend=primary[association['backend_object_id']]
    bad=bytearray(data);struct.pack_into('<Q',bad,backend.body+168,association['source_owner_object_id']);reject('Backend owner changed to other actual feature',bytes(bad))
    support=primary[association['support_object_id']]
    support_count=struct.unpack_from('<I',data,support.body+8)[0]
    bad=bytearray(data);struct.pack_into('<Q',bad,support.body+13+19*support_count,descriptor.object_id+1);reject('Reciprocal support descriptor changed',bytes(bad))
    # Same-width recipe term substitution creates a valid complete tuple naming an EDGE, not a VERTEX.
    original=data[recipe.body:recipe.end];start=original.index(b'5')
    bad=bytearray(data);bad[recipe.body+start]=ord('1');reject('Direct complete group names wrong topology kind',bytes(bad))
    term_pattern=struct.pack('<I',1)+b'1'+struct.pack('<IIiI',0,1,300,0)
    term_position=original.index(term_pattern)
    bad=bytearray(data);bad[recipe.body+term_position+4]=ord('2');reject('Named EDGEs fail complete incident-edge set',bytes(bad))
    mapping=primary[association['mapping_record_object_id']]
    bad=bytearray(data);struct.pack_into('<Q',bad,mapping.body+6,99);reject('Native stored handle lacks same-blob BODY identifier',bytes(bad))
    blob_member=association['history_blob_member'];blob=members[blob_member];parsed=inspect_asm(blob)
    tags=decode_asm_generic_tags(blob,parsed,allow_fpm_tracking=True)
    duplicate=next(t for t in tags['tags'] if t['owner_kind']=='vertex' and t['terms'][0]['name']=='6' and t['terms'][0]['stored_reference_components_int32']==[300])
    name_token=parsed['records'][duplicate['attribute_record_index']]['tokens'][12]
    badblob=bytearray(blob);badblob[name_token['offset']+2]=ord('5')
    badmembers=dict(members);badmembers[blob_member]=bytes(badblob)
    reject('Duplicate exact complete VERTEX group blocks uniqueness',altered_members=badmembers)
    for relative in ['scaleshellinputs-97ef1cfd19e4/scale_vertex.f3d',
                     'pipeedgecontrasts-5bd287323ae7/line_full.f3d',
                     'loftpointholdouts-bb91509a13e4/vertex_construction_sharp_end.f3d']:
        ms=read_members(ROOT/relative,zstd_library);model=decode_basics(ROOT/relative,zstd_library);s=model['streams'][0];m=s['member'];d=ms[m]
        rs,_=design_records(d,ms[m.replace('BulkStream.dat','MetaStream.dat')]);before=copy.deepcopy(s['features'])
        result=decode_named_vertex_selections(d,rs,s['features'],m,ms,s['body_asm_identifiers'])
        assert not result['associations'] and s['features'] == before
        report['old_controls'].append({'file':relative,'no_new_association':True,'features_unchanged':True})
    report['summary']={'actual_capture_archives':2,'direct_named_vertex_associations':2,'reciprocal_incident_edge_associations':4,
        'API_coordinate_agreements_after_identity':2,'unresolved_auxiliary_face_groups_retained':1,
        'legacy_incidence_warnings_retained':2,'guards':len(report['guards']),'old_controls':len(report['old_controls'])}
    return report


RECIPE_TARGETS = {'loftbrepends-e07e3859ed20/edge_both_tangent.f3d': [445, 452], 'loftbrepends-e07e3859ed20/edge_end_smooth_weight1_25.f3d': [399], 'loftbrepends-e07e3859ed20/edge_end_tangent_weight1_5.f3d': [399], 'loftbrepends-e07e3859ed20/edge_start_free.f3d': [396], 'loftbrepends-e07e3859ed20/face_end_free.f3d': [400], 'loftfaces-055501f619c5/edge_path_smooth_weight1.f3d': [399], 'loftfaces-055501f619c5/edge_path_tangent_weight1.f3d': [399], 'loftfaces-055501f619c5/edge_path_tangent_weight2.f3d': [399], 'loftfaces-055501f619c5/face_free.f3d': [400], 'loftpointholdouts-bb91509a13e4/vertex_construction_sharp_end.f3d': [333], 'pipeedgecontrasts-5bd287323ae7/line_full.f3d': [344], 'pipeedgecontrasts-5bd287323ae7/line_offset_negative_partial.f3d': [344], 'pipeedgecontrasts-5bd287323ae7/line_partial.f3d': [344], 'pipepaths-3d11bd427946/brep_edge_circular.f3d': [320], 'scaleshellinputs-97ef1cfd19e4/scale_vertex.f3d': [308], 'sketchprojections-67c0c4531b8f/body_edge.f3d': [322, 324, 344, 346], 'specialfillets-d50f7a4f04e0/rule_all_both.f3d': [428, 434, 440, 446, 450, 454, 458, 460], 'specialfillets-d50f7a4f04e0/rule_all_rounds.f3d': [424, 430, 436, 440], 'specialfillets-d50f7a4f04e0/rule_asymmetric.f3d': [431, 437, 443, 449, 453, 457, 461, 463], 'surfacebounds-ac801bb00fae/extend_perpendicular.f3d': [304, 306], 'surfacebounds-ac801bb00fae/extend_perpendicular_negative.f3d': [304, 306], 'surfacebounds-ac801bb00fae/extend_tangent.f3d': [304, 306], 'surfacebounds-ac801bb00fae/ruled_direction.f3d': [329, 345], 'surfacebounds-ac801bb00fae/ruled_mitered.f3d': [318, 330], 'surfacebounds-ac801bb00fae/ruled_normal.f3d': [328, 332], 'surfacebounds-ac801bb00fae/ruled_tangent.f3d': [318, 330], 'surfacetools-856ca50cf4c7/offset_negative.f3d': [308, 310, 312, 314], 'surfacetools-856ca50cf4c7/offset_positive.f3d': [308, 310, 312, 314], 'surfacetools-856ca50cf4c7/offset_rounded.f3d': [308, 310, 312, 314], 'sweepprofiles-8d489fe02d2d/open_brep_edge_surface.f3d': [386, 388], 'sweepprofiles-b2b7a2774752/open_brep_edge_surface.f3d': [386, 388], 'sweepprofiles-b2b7a2774752/planar_face.f3d': [591, 593, 595, 597], 'sweepprofiles-f20861d6c5c2/open_brep_edge_partial.f3d': [386, 388], 'sweepprofiles-f20861d6c5c2/open_brep_edge_reversed.f3d': [386, 388]}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--output'); parser.add_argument('--probe', action='store_true'); parser.add_argument('--zstd-library'); args=parser.parse_args()
    library=args.zstd_library or next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib'))
    report=validate_probe(library) if args.probe else validate(library); output=args.output or ('named-vertex-selection-decoding.json' if args.probe else 'named-vertex-selection-feasibility.json'); Path(output).write_text(json.dumps(report, indent=2)+'\n'); print(json.dumps(report['summary'],indent=2))

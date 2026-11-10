"""Stored GenerateFaceGroups asset before a typed later CombineFaceGroups.

The independently selected current mesh keeps its current asset. Stored feature
assets are neither promoted to current geometry nor paired by coordinate order.
"""
import copy
import lzma
import math
import struct

from decode_mesh_face_groups import decode_mesh_face_groups, FACE_GROUPS
from decode_mesh_combine_face_groups import decode_mesh_combine_face_groups
from decode_mesh_geometry_variants import decode_mesh_contents_variants
from decode_sketch import reference
from decode_timeline import decode_timeline

OLD_REASON='FaceGroups selected mesh current asset route unresolved'
SCOPE=('Observed historical Fast20/minimum-size0.02 GenerateFaceGroups controls and explicit definition39 '
       'eight-triangle stored feature cache, linked by the same native selected mesh and a later '
       'CombineFaceGroups additional asset in a unique explicit native history. Current mesh/asset '
       'ownership stays independent; asset50 temporal role, persistent group identity, algorithms and lifecycle replay unresolved.')


def decode_historical_mesh_face_groups(data,records,features,member,members,mesh_contents=None):
    """Return decoded/unresolved/scope; rows feature_object_id/kind/name/settings/route."""
    records=list(records);result=dict(decoded=[],unresolved=[],scope=SCOPE)
    if not any(r.is_primary and r.class_guid==FACE_GROUPS for r in records):return result
    meshes=mesh_contents if mesh_contents is not None else decode_mesh_contents_variants(data,records,member,members)
    strict=decode_mesh_face_groups(data,records,features,member,members,meshes)
    candidates={u['feature_object_id'] for u in strict['unresolved'] if u['reason']==OLD_REASON}
    if not candidates:return result
    expanded=decode_mesh_face_groups(data,records,features,member,members,meshes,allow_stored_feature_asset=True)
    rows={row['feature_object_id']:row for row in expanded['decoded']}
    errors={u['feature_object_id']:u['reason'] for u in expanded['unresolved']}
    combinations=decode_mesh_combine_face_groups(data,records,features,member,members,meshes)
    timeline=decode_timeline(data,records,copy.deepcopy(features))
    for identity in sorted(candidates):
        try:
            if identity not in rows:raise ValueError(errors.get(identity,'Historical FaceGroups common controls unresolved'))
            row=rows[identity];settings=row['settings'];asset=settings.get('stored_feature_asset')
            if (not asset or settings.get('stored_feature_asset_is_current') is not False
                    or settings['stored_method_code']!=0
                    or settings['scalar_bindings']['Angle Threshold']['stored_value']!=math.radians(20)
                    or settings['minimum_face_group_size']!=0.02
                    or settings['triangle_face_groups']['decoded_triangle_face_group_temporary_ids']!=list(range(1,9))):
                raise ValueError('Unobserved historical FaceGroups control/cache family')
            matches=[c for c in combinations['decoded']
                if c['settings']['native_mesh_object_id']==settings['native_mesh_object_id']
                and c['settings']['additional_stored_asset']==asset
                and c['settings']['current_mesh_asset']==settings['selected_current_mesh_asset']]
            if len(matches)!=1:raise ValueError('Historical FaceGroups matching later Combine asset/mesh route absent or ambiguous')
            combine=matches[0];cid=combine['feature_object_id']
            histories=[s for s in timeline['sequences'] if identity in s['native_entry_object_ids'] and cid in s['native_entry_object_ids']]
            if len(histories)!=1:raise ValueError('Historical FaceGroups shared explicit native history missing or ambiguous')
            history=histories[0];ids=history['native_entry_object_ids']
            if ids.index(identity)>=ids.index(cid):raise ValueError('Historical FaceGroups does not precede Combine in native history')
            primaries=[r for r in records if r.is_primary and r.object_id==identity]
            if len(primaries)!=1:raise ValueError('Historical FaceGroups primary record ambiguous')
            record=primaries[0];body=data[record.body:record.end]
            if reference(body,39)!=asset['asset_object_id'] or reference(body,50)!=settings['additional_stored_asset']['asset_object_id']:
                raise ValueError('Historical FaceGroups explicit asset operands disagree')
            selected=[m for m in meshes['decoded'] if m['mesh_object_id']==settings['native_mesh_object_id']]
            if len(selected)!=1:raise ValueError('Historical FaceGroups selected current mesh identity ambiguous')
            selected=selected[0]
            route=dict(feature_object_id=identity,selected_native_mesh_object_id=settings['native_mesh_object_id'],
                selected_current_mesh_route={key:selected[key] for key in (
                    'mesh_record_offset','feature_object_id','native_feature_class_guid','feature_owner_scope',
                    'component_object_id','mesh_collection_object_id','collection_mesh_object_ids',
                    'asset_object_id','asset_record_offset','asset_filename_object_id','asset_member',
                    'asset_fusion_uuid','asset_reference_field_offset','stored_matrix_copies',
                    'asset_coordinates_to_component_matrix','matrix_scope')},
                stored_feature_asset_object_id=asset['asset_object_id'],stored_feature_asset_member=asset['asset_member'],
                selected_current_asset_object_id=settings['selected_current_mesh_asset']['asset_object_id'],
                selected_current_asset_member=settings['selected_current_mesh_asset']['asset_member'],
                following_combine_feature_object_id=cid,
                following_combine_additional_asset_object_id=combine['settings']['additional_stored_asset']['asset_object_id'],
                association='Same typed native mesh and equal explicit asset identities; no coordinate/name/array-order identity join',
                history=dict(history_record_object_id=history['history_record_object_id'],owner_object_id=history['owner_object_id'],
                    native_entry_object_ids=ids,feature_native_entry_index=ids.index(identity),combine_native_entry_index=ids.index(cid)),
                feature_asset_reference_offset=record.body+39,additional_asset_reference_offset=record.body+50,
                feature_body_offset=record.body,feature_body_end_offset=record.end,stored_feature_body_hex=body.hex(),
                asset50_temporal_role=None,scope=SCOPE)
            result['decoded'].append(dict(feature_object_id=identity,kind=row['kind'],name=row['name'],settings=settings,route=route))
        except (ValueError,KeyError,IndexError,TypeError,UnicodeError,struct.error,lzma.LZMAError) as error:
            result['unresolved'].append(dict(feature_object_id=identity,class_guid=FACE_GROUPS,reason=str(error)))
    return result

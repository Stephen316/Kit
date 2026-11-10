"""Bounded datum Mirror reflection using an explicitly owned custom support.

Observed source Offset plus selected Offset/Angle support, exact three-plane
collection, and independently scoped source/support/Mirror owners. Identity is
established by native references before Householder/cache corroboration.
"""
from copy import deepcopy
import struct

from decode_dependencies import decode_dependencies
from decode_mirror_datum_outputs import decode_mirror_datum_outputs, PLANE
from decode_mirror_datum_reflections import reflection_matrix
from decode_parameters import read_string
from decode_plane_definitions import decode_plane_definitions
from decode_remaining_body_inputs import MIRROR_DATUM, _access
from decode_selection import known_construction_entities, native_origin_entities
from decode_sketch import attributes, reference, same

COLLECTION = 'A8635B5F-1E2C-45FD-8BA9-0173B0FEB75E'
WORKPLANE = 'D869265F-F339-4751-A066-91D30F81FF08'
SCOPE = ('Observed same-component datum Mirror with a separately owned Offset/Angle '
         'construction-plane support and exact three-plane collection; computed '
         'reflection corroborated by owned output cache; general regeneration unresolved')


def decode_datum_mirror_supports(data, records, features, assembly):
    """Return decoded/unresolved/scope; original origin-plane helper is unchanged."""
    candidates=[f for f in features if f['class_guid']==MIRROR_DATUM]
    if not candidates:
        return dict(decoded=[],unresolved=[],scope=SCOPE)
    records=list(records)
    primary,typed=_access(data,records)
    copies=deepcopy(features)
    definitions=decode_plane_definitions(data,records,copies)
    byplane={}
    for definition in definitions['definitions']:
        byplane.setdefault(definition['plane_object_id'],[]).append(definition)
    successful={d['feature_object_id'] for d in definitions['definitions']}
    known=known_construction_entities(data,records,[f for f in copies
        if f['kind']!='ConstructionPlane' or f['object_id'] in successful])
    origins=native_origin_entities(data,records)
    decoded,unresolved=[],[]
    for feature in candidates:
        try:
            record,body=typed(feature['object_id'],MIRROR_DATUM)
            if record.start!=feature['record_offset']:
                raise ValueError('Custom-support Mirror feature record identity disagrees')
            provenance=decode_mirror_datum_outputs(data,records,body,feature,known)
            selected=provenance['mirror_plane']['entity']
            # Origin selections are owned by the existing strict helper. They are
            # neither recovered nor rejected by this separate custom-support stage.
            if selected['object_id'] in origins:
                continue
            source,output=provenance['source_plane'],provenance['output_plane']
            support_id=selected['object_id']
            choices=byplane.get(support_id,[])
            sources=byplane.get(source['native_plane_object_id'],[])
            if len(choices)!=1 or len(sources)!=1:
                raise ValueError('Source/selected support does not have one freshly decoded owned plane definition')
            support_definition,source_definition=choices[0],sources[0]
            support_geometry=support_definition['cached_geometry']
            if (source_definition['definition_kind']!='Offset'
                    or support_definition['definition_kind'] not in ('Offset','Angle')):
                raise ValueError('Unobserved custom-support/source plane definition combination')
            source_owner=source['owner_feature_object_id']
            support_owner=support_definition['feature_object_id']
            owners_ids=(source_owner,support_owner,feature['object_id'])
            if (len(set(owners_ids))!=3 or source_definition['feature_object_id']!=source_owner
                    or selected.get('feature_object_id')!=support_owner):
                raise ValueError('Source/support/Mirror feature owners are not three explicit distinct identities')
            typed(source_owner,WORKPLANE);typed(support_owner,WORKPLANE)
            collection_id=source['scope_reference_object_id']
            if output['scope_reference_object_id']!=collection_id:
                raise ValueError('Custom-support source/output plane collections disagree')
            _,collection=typed(collection_id,COLLECTION)
            count=struct.unpack_from('<I',collection,2)[0]
            if collection[:2]!=bytes(2) or count!=3 or len(collection)!=51+22*count:
                raise ValueError('Unobserved custom-support three-plane collection framing')
            members=[reference(collection,6+11*i) for i in range(count)]
            repeated=len(collection)-15-11*count
            expected={source['native_plane_object_id'],support_id,output['native_plane_object_id']}
            if (len(expected)!=3 or len(set(members))!=count or set(members)!=expected
                    or struct.unpack_from('<I',collection,repeated)[0]!=count
                    or [reference(collection,repeated+4+11*i) for i in range(count)]!=members):
                raise ValueError('Custom-support collection repeated source/support/output membership disagrees')
            component_id=reference(collection,len(collection)-11)
            typed(component_id,'E03784ED-5E19-4E14-B9F2-3B07017018CD')
            # The selected cache is independently validated by the existing full
            # plane definition parser. Check its collection pointer explicitly.
            _,support_body=typed(support_id,PLANE)
            _,cursor=attributes(support_body,2)
            _,end=read_string(support_body,cursor+109)
            if (reference(support_body,end)!=collection_id
                    or reference(support_body,end+20)!=support_owner):
                raise ValueError('Selected custom support cache collection/feature owner disagrees')
            for plane in (source,output):
                _,chunk=typed(plane['native_plane_object_id'],PLANE)
                if reference(chunk,len(chunk)-11)!=collection_id:
                    raise ValueError('Custom-support plane cache/collection footer disagrees')
            if reference(support_body,len(support_body)-11)!=collection_id:
                raise ValueError('Selected support plane cache/collection footer disagrees')
            if (not same(source_definition['cached_geometry']['plane_to_component_matrix'],source['cached_plane_to_component_matrix'])
                    or not same(selected['origin_cm'],support_geometry['origin_cm'])
                    or not same(selected['normal'],support_geometry['normal'])):
                raise ValueError('Selected/source geometry disagrees with freshly decoded owned plane definition')
            owners=[{'object_id':identity} for identity in owners_ids]
            decode_dependencies(data,records,owners,assembly)
            if any(owner.get('component_object_id')!=component_id or 'component_scope_object_id' not in owner for owner in owners):
                raise ValueError('Source/support/Mirror native dependency scopes disagree')
            matrix=reflection_matrix(support_geometry['origin_cm'],support_geometry['normal'])
            source_matrix=source['cached_plane_to_component_matrix']
            computed=[sum(matrix[4*r+k]*source_matrix[4*k+c] for k in range(4)) for r in range(4) for c in range(4)]
            cached=output['cached_plane_to_component_matrix']
            if not same(computed,cached):
                raise ValueError('Custom-support reflection does not match explicitly owned output plane cache')
            decoded.append(dict(feature_object_id=feature['object_id'],feature_class_guid=MIRROR_DATUM,
                input_kind='ConstructionPlane',input_count=1,component_object_id=component_id,
                source_plane_object_id=source['native_plane_object_id'],
                support_plane_object_id=support_id,output_plane_object_id=output['native_plane_object_id'],
                source_output_provenance=provenance,selected_support_definition=support_definition,
                native_component_evidence=dict(plane_collection_object_id=collection_id,
                    stored_plane_object_ids=members,repeated_plane_object_ids=members,
                    uninterpreted_collection_middle_hex=collection[6+11*count:repeated].hex(),
                    dependency_scopes=[dict(feature_object_id=owner['object_id'],scope_object_id=owner['component_scope_object_id'],
                        component_object_id=owner['component_object_id']) for owner in owners]),
                is_combine=None,stitch_tolerance_cm=None,
                computed_reflection_matrix=matrix,computed_output_plane_frame=computed,
                stored_output_plane_frame=cached,maximum_frame_difference=max(abs(a-b) for a,b in zip(computed,cached)),
                matrix_scope='Computed Householder reflection in the explicitly shared native component; determinant -1, not a stored matrix or proper rigid occurrence transform',
                output_scope='Explicit native association/owner identifies output before cache corroboration; unavailable API resultFeatures/timeline/definition members are not invented',
                unresolved_controls=['Combine and stitch tolerance have no applicable successful datum getters',
                    'Other datum/support layouts, generalized lifecycle replay and assembly solving'],scope=SCOPE))
        except (ValueError,IndexError,KeyError,UnicodeError,struct.error) as error:
            unresolved.append(dict(feature_object_id=feature['object_id'],reason=str(error)))
    return dict(decoded=decoded,unresolved=unresolved,scope=SCOPE)

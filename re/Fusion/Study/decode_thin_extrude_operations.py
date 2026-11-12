"""Observed one-sided Thin Extrude Boolean controls and native body-list evidence."""
import struct

from decode_extrude import decode_extrude
from decode_thin_extrudes import EXTRUDE,inspect_thin_extrude

OPERATIONS=('Join','Cut','Intersect')
SCOPE=('Observed solid one-sided untapered distance Thin Extrude Join/Cut/Intersect, Side1 wall with owned '
       'positive thickness and one closed four-Line sketch profile. Historical target selection, newly owned '
       'BODY anchors and current native collection facts remain distinct; topology/lifecycle and regeneration unresolved.')


def decode_thin_extrude_operations(data,records,features):
    """Additional operation summary; default Thin Extrude/common dictionaries unchanged."""
    result=dict(decoded=[],unresolved=[],scope=SCOPE)
    for feature in features:
        if feature.get('kind')!='Extrude' or feature.get('class_guid')!=EXTRUDE:
            continue
        if not any(p.get('role')=='Side1WallThickness' for p in feature.get('parameters',[])):
            continue
        choices=[r for r in records if r.is_primary and r.object_id==feature['object_id']]
        if len(choices)!=1:continue
        record=choices[0];body=data[record.body:record.end]
        try:
            common,reasons=decode_extrude(body,feature)
            if common['operation']['kind'] not in OPERATIONS:continue
            from decode_thin_extrude_body_routes import resolve_thin_extrude_body_routes
            row=inspect_thin_extrude(data,records,body,feature,features=features,
                allowed_operations=OPERATIONS,body_list_resolver=resolve_thin_extrude_body_routes)
            if not row['is_thin_extrude']:
                raise ValueError('Thin Boolean role bindings disagree with actual native thin flag')
            metadata=row['thin_metadata'];profile=row['profile']
            loops=profile.get('loops',[])
            if (reasons or common['extent']['mode']!='OneSided'
                    or metadata['side_one']['stored_wall_location_code']!=0 or metadata['side_two']['applicable'] is not False
                    or profile.get('kind')!='SketchProfile' or len(loops)!=1
                    or len(loops[0].get('curve_references',[]))!=4
                    or any(curve.get('entity_kind')!='Line' for curve in loops[0]['curve_references'])):
                raise ValueError('Unsupported Thin Boolean side/profile combination outside observed one-sided Side1 four-Line family')
            if row['common_extrusion_controls']!=common:
                raise ValueError('Thin Boolean inspection/common controls disagree')
            row['scope']=SCOPE
            row['geometry_status']='Thin Boolean wall controls, closed source profile and typed target/new-anchor/current body-list provenance; geometric regeneration and persistent topology unresolved'
            result['decoded'].append(row)
        except (ValueError,KeyError,IndexError,TypeError,UnicodeError,struct.error) as error:
            result['unresolved'].append(dict(feature_object_id=feature['object_id'],class_guid=EXTRUDE,reason=str(error)))
    return result

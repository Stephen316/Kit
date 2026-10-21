"""Observed fixed-NURBS Sweep paths with reused common controls/profile decoding."""
import struct

from decode_selection import resolve_single_sketch_curve
from decode_sweep_modes import SWEEP,decode_sweep_modes

SCOPE=('Observed solid full-distance perpendicular NewBody Sweep with one circular sketch profile and '
       'one open fixed cubic NURBS path, including polynomial/rational and multispan sources. Explicit '
       'source identity, local/component caches and numeric controls retained; traversal opposition, '
       'general profile frames, swept surfaces, lifecycle and regeneration unresolved.')


class _NotFixedPath(ValueError):
    """Leave other default Sweep source families untouched."""


def decode_sweep_fixed_spline_paths(data,records,features):
    """Return decoded/unresolved/scope; successful rows feature_object_id/kind/name/settings."""
    result=dict(decoded=[],unresolved=[],scope=SCOPE)
    primary={}
    for record in records:
        if record.is_primary:primary.setdefault(record.object_id,[]).append(record)
    for feature in features:
        if feature.get('class_guid')!=SWEEP:continue
        activated=[]
        def resolver(d,rs,path_id,owner_id,source_features):
            try:resolve_single_sketch_curve(d,rs,path_id,owner_id,source_features,('FixedSpline',))
            except (ValueError,KeyError,IndexError,struct.error) as error:raise _NotFixedPath() from error
            activated.append(path_id)
            from decode_sweep_fixed_spline_sources import resolve_sweep_fixed_spline_path
            return resolve_sweep_fixed_spline_path(d,rs,path_id,owner_id,source_features)
        try:
            rows=primary.get(feature['object_id'],[])
            if len(rows)!=1 or rows[0].class_guid!=SWEEP:
                raise ValueError('Fixed-NURBS Sweep feature primary identity ambiguous')
            record=rows[0]
            if feature.get('record_offset')!=record.start:
                raise ValueError('Fixed-NURBS Sweep feature metadata differs from native record')
            settings=decode_sweep_modes(data,records,data[record.body:record.end],feature,features,path_resolver=resolver)
            source=settings['path'];profile=settings['profile'];loops=profile.get('loops',[]) if isinstance(profile,dict) else []
            if (settings['operation']!='NewBody' or not settings['is_solid'] or settings['sweep_mode']!='SinglePathPerpendicular'
                    or settings['path_fraction']!=1. or settings['stored_against_path_fraction']!=0.
                    or settings['guide_surfaces'] or settings['stored_guide_rail'] is not None
                    or settings['taper_angle_radians']!=0. or settings['twist_angle_radians']!=0.
                    or source['count']!=1 or source['segments'][0]['kind']!='FixedSpline' or source['is_closed']
                    or len(loops)!=1 or loops[0].get('is_outer') is not True
                    or len(loops[0].get('curve_references',[]))!=1
                    or loops[0]['curve_references'][0].get('entity_kind')!='Circle'):
                raise ValueError('Unsupported fixed-NURBS Sweep outside captured solid/full/perpendicular/circular NewBody family')
            result['decoded'].append(dict(feature_object_id=feature['object_id'],kind='Sweep',name=feature.get('name'),settings=settings))
        except _NotFixedPath:
            continue
        except (ValueError,KeyError,TypeError,IndexError,UnicodeError,struct.error) as error:
            if activated:result['unresolved'].append(dict(feature_object_id=feature['object_id'],class_guid=SWEEP,reason=str(error)))
    return result

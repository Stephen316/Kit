"""Stored interpolation-width fillet definition and rational XYZ approximation.

This is not the exact procedural fillet surface. Native sentinel scalars and
axis/trailer flags are retained without inferred tolerance or periodic meaning.
"""
import math

from decode_bspline import knot_vector, scalar_lists
from decode_fillet_spline_caches import _expect, _prefix
from decode_pcurve_variants import encode_pcurve_fields
from decode_rule_blend_cache import _bounds, _surface_grid

SCOPE = ('Stored finite straight-spine/interpolation-width fillet definition and rational bicubic XYZ '
         'approximation; API radius/position corroboration is separate from cache evaluation, exact '
         'procedural construction, approximation bounds, surface sense and lifecycle remain unresolved')


def decode_interp_blend_cache(record):
    """Strict captured mode0/interp branch; existing Variable/Rule defaults stay strict."""
    ts = _prefix(record, 'spline-surface', 'srf_srf_v_bl_spl_sur', False)
    for index,kind,value in ((0,'pointer',-1),(1,'integer',-1),(2,'pointer',-1)):
        _expect(ts,index,kind,value)
    supports=[];cursor=7
    for _ in range(2):
        beginning=cursor
        _expect(ts,cursor,'string','blend_support_surface')
        _expect(ts,cursor+1,'entity_name','plane')
        origin=_expect(ts,cursor+2,'position_vector')
        normal=_expect(ts,cursor+3,'direction_vector')
        axis=_expect(ts,cursor+4,'direction_vector')
        for offset in range(5,10):_expect(ts,cursor+offset,'boolean_token',False)
        for offset,value in ((10,'null_curve'),(11,'nullbs'),(13,'nullbs'),(15,'nullbs')):
            _expect(ts,cursor+offset,'entity_name',value)
        auxiliary=_expect(ts,cursor+12,'position_vector');_expect(ts,cursor+14,'integer',0)
        if (not math.isclose(sum(x*x for x in normal),1.,abs_tol=1e-12)
                or not math.isclose(sum(x*x for x in axis),1.,abs_tol=1e-12)
                or not math.isclose(sum(a*b for a,b in zip(normal,axis)),0.,abs_tol=1e-12)):
            raise ValueError('Interp blend support plane frame is not orthonormal')
        cursor+=16
        supports.append(dict(kind='plane',raw_origin=origin,raw_normal=normal,raw_reference_axis=axis,
            stored_auxiliary_vector=auxiliary,stored_definition=ts[beginning:cursor]))
    _expect(ts,cursor,'entity_name','straight')
    origin=_expect(ts,cursor+1,'position_vector');direction=_expect(ts,cursor+2,'direction_vector')
    spine_bounds,spine_flags,cursor=_bounds(ts,cursor+3,2)
    if spine_flags!=[True,True] or not spine_bounds[0]<spine_bounds[1] or not math.isclose(sum(x*x for x in direction),1.,abs_tol=1e-12):
        raise ValueError('Interp blend requires finite ordered straight-spine bounds and unit direction')
    leading_scalars=[_expect(ts,cursor+i,'double',0.) for i in (0,1)]
    _expect(ts,cursor+2,'enum',0);cursor+=3
    width_start=cursor
    _expect(ts,cursor,'entity_name','interp');_expect(ts,cursor+1,'enum',0)
    _expect(ts,cursor+2,'boolean_token',True)
    width_interval=[_expect(ts,cursor+i,'double') for i in (3,4)];cursor+=5
    _expect(ts,cursor,'entity_name','nubs');degree=_expect(ts,cursor+1,'integer',5)
    _expect(ts,cursor+2,'enum',0)
    knots,compact,count,cursor=knot_vector(ts,cursor+4,_expect(ts,cursor+3,'integer'),degree)
    flat=[_expect(ts,cursor+i,'double') for i in range(2*count)];cursor+=2*count
    width=dict(degree=degree,knots=knots,stored_compact_knots=compact,
        raw_control_points=[flat[i:i+2] for i in range(0,len(flat),2)],weights=[],is_rational=False,
        stored_form_code=0,parameter_domain=[knots[degree],knots[-degree-1]])
    if (width_interval!=width['parameter_domain'] or not width_interval[0]<width_interval[1]
            or any(p[0]<=0 or p[1]!=0 for p in width['raw_control_points'])):
        raise ValueError('Interp blend width domain/control-coordinate layout differs')
    _expect(ts,cursor,'enum',2);row_count=_expect(ts,cursor+1,'integer');cursor+=2
    if row_count not in (3,4):raise ValueError('Unobserved interp blend row count')
    rows=[]
    for _ in range(row_count):
        beginning=cursor
        parameter=_expect(ts,cursor,'double');value=_expect(ts,cursor+1,'double')
        auxiliary=[_expect(ts,cursor+i,'double',1e37) for i in (2,3)]
        point=_expect(ts,cursor+4,'position_vector');tangent=_expect(ts,cursor+5,'direction_vector')
        if (value<=0 or not width_interval[0]<=parameter<=width_interval[1]
                or (rows and parameter<=rows[-1]['parameter'])
                or any(not math.isclose(a,b,abs_tol=1e-12) for a,b in zip(point,[o+parameter*d for o,d in zip(origin,direction)]))
                or tangent!=direction):
            raise ValueError('Interp blend row parameter/value/spine fields disagree')
        cursor+=6
        rows.append(dict(parameter=parameter,width_scalar=value,literal_auxiliary_scalars=auxiliary,
            raw_spine_point=point,raw_spine_direction=tangent,stored_token_start=beginning,stored_token_end=cursor))
    if [rows[0]['parameter'],rows[-1]['parameter']]!=width_interval:
        raise ValueError('Interp blend rows do not cover stored width interval')
    width_end=cursor
    _expect(ts,cursor,'enum',0)
    pregrid_bounds,pregrid_flags,cursor=_bounds(ts,cursor+1,4)
    if pregrid_flags not in ([True,True,False,False],[True,True,True,False]) or pregrid_bounds[:2]!=[0.,1.]:
        raise ValueError('Unobserved interp blend pre-grid bounds')
    _expect(ts,cursor,'integer',1)
    metadata_scalars=[_expect(ts,cursor+i,'double') for i in (1,2)]
    if any(v<=0 for v in metadata_scalars):raise ValueError('Interp blend metadata scalar is not positive')
    _expect(ts,cursor+3,'integer',1);_expect(ts,cursor+4,'enum',0);cursor+=5
    grid_start=cursor
    cache,cursor=_surface_grid(ts,cursor,allowed_axis_flags=((0,0,0,0),(0,0,0,1)))
    trailer_start=cursor
    scalar=_expect(ts,cursor,'double')
    lists,cursor=scalar_lists(ts,cursor+1,6)
    _expect(ts,cursor,'boolean_token',False)
    for offset in (1,2,3):_expect(ts,cursor+offset,'integer',0)
    _expect(ts,cursor+4,'entity_name','null_curve')
    trailer_flags=[_expect(ts,cursor+i,'boolean_token',v) for i,v in ((5,True),(6,True),(7,False),(8,False))]
    _expect(ts,cursor+9,'entity_name','nullbs');_expect(ts,cursor+10,'entity_name','nullbs')
    _expect(ts,cursor+11,'subtype_end')
    bounds,bound_flags,cursor=_bounds(ts,cursor+12,4)
    if cursor!=len(ts) or bound_flags!=[True]*4:
        raise ValueError('Interp blend outer interval/trailing fields differ')
    for interval,domain in ((bounds[:2],cache['parameter_domain_u']),(bounds[2:],cache['parameter_domain_v'])):
        if not interval[0]<interval[1] or interval[0]<domain[0]-1e-12 or interval[1]>domain[1]+1e-12:
            raise ValueError('Interp blend trim interval outside stored tensor domain')
    cache.update(stored_parameter_interval_u=bounds[:2],stored_parameter_interval_v=bounds[2:],
        stored_outer_bound_flags=bound_flags,stored_wrapper_flag=False,stored_spine_kind='straight',
        stored_spine=dict(raw_origin=origin,raw_direction=direction,stored_bounds=spine_bounds,stored_bound_flags=spine_flags),
        stored_support_definitions=supports,stored_leading_scalars=leading_scalars,stored_blend_mode_code=0,
        stored_width_kind='interp',stored_width_parameter_interval=width_interval,stored_interp_width_cache=width,
        stored_interp_rows=rows,stored_interp_row_layout_code=2,stored_interp_width_definition=ts[width_start:width_end],
        stored_pregrid_bounds=pregrid_bounds,stored_pregrid_bound_flags=pregrid_flags,
        stored_pregrid_positive_scalars=metadata_scalars,stored_grid_start_token=grid_start,
        stored_procedural_definition=ts[5:grid_start],stored_cache_trailer_scalar=scalar,
        stored_trailer_scalar_lists=lists,stored_post_grid_flags=trailer_flags,stored_cache_trailer=ts[trailer_start:],
        stored_complete_payload_hex=encode_pcurve_fields(ts).hex(),procedural_subtype='srf_srf_v_bl_spl_sur',
        representation='Stored rational bicubic interpolation-width blend approximation; exact procedural fillet not reconstructed',
        cache_status='No resulting API surface-grid/evaluator capture; tensor evaluation is of serialized approximation only, with unbounded approximation error',
        width_status='Stored two-coordinate degree-five polynomial and interpolation rows; API radius/position correspondence is separately corroborated for captured rows only',
        periodicity_status='Native axis flags preserved literally, including last-axis code1; no periodicity/form meaning assigned',
        flag_scope='Sentinel1e37 values, optional bounds and trailer flags retained without parameter reversal, tolerance or derivative interpretation',
        coordinate_scope='Raw ASM asset frame; source/body/component/occurrence transforms are not applied',scope=SCOPE)
    return cache

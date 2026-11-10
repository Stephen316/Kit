"""SurfaceOffset source facade retaining the strict default reader separately."""
from decode_surface_offset_sources import decode_surface_offset_sources as _decode


def decode_surface_offset_sources(data, records, features, member, members,
                                  body_identifier_summary, body_selections=None):
    """Opt in to the observed typed support/face-intersection family only."""
    return _decode(data, records, features, member, members, body_identifier_summary,
        body_selections, allow_face_intersection_sources=True)

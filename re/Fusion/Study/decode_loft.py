"""Read observed Loft operations, face/point sections and sketch guides."""

import struct

from decode_loft_modes import LOFT_GUID, SECTION_GUID
from decode_loft_operations import decode_loft_operations
from decode_loft_faces import decode_loft_faces
from decode_loft_brep_ends import decode_loft_brep_ends
from decode_loft_points import decode_loft_points
from decode_loft_point_extensions import decode_loft_point_extensions
from decode_loft_curved_guides import decode_loft_curved_guides
from decode_loft_composite_guides import decode_loft_composite_guides


def decode_loft(data, records, body, feature, features):
    reasons = []
    for reader in (decode_loft_operations, decode_loft_faces, decode_loft_brep_ends, decode_loft_points, decode_loft_point_extensions, decode_loft_curved_guides, decode_loft_composite_guides):
        try:
            return reader(data, records, body, feature, features)
        except (ValueError, KeyError, IndexError, struct.error) as error:
            reasons.append(reader.__name__+": "+str(error))
    raise ValueError("Unsupported observed Loft variant; "+"; ".join(reasons))

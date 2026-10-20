"""Dispatch observed Sweep profile, guide, operation and solid-body variants."""

import struct

from decode_sweep_single_path import SWEEP_GUID, decode_sweep as decode_single_path
from decode_sweep_operations import decode_sweep_operations
from decode_sweep_profiles import decode_sweep_profiles
from decode_solid_sweep import decode_solid_sweep


def decode_sweep(data, records, body, feature, features):
    reasons = []
    for reader in (decode_single_path, decode_sweep_operations, decode_sweep_profiles, decode_solid_sweep):
        try:
            return reader(data, records, body, feature, features)
        except (ValueError, KeyError, IndexError, struct.error) as error:
            reasons.append(reader.__name__+": "+str(error))
    raise ValueError("Unsupported observed Sweep variant; "+"; ".join(reasons))

"""Observed symmetric suppression lattice rule with discriminating boundaries.

Native role lists still establish every source/member ID. This module derives
indices from quantity/symmetry controls; it never selects IDs from coordinates.
"""

import math

from decode_sketch import same
from decode_sketch_pattern_coverage import decode_sketch_pattern_coverage


def symmetric_seed_lattice_index(settings, total):
    """Return the derived seed index within the bounded observed pattern modes."""
    if settings["kind"] == "SketchCircularPattern":
        quantity = settings["quantity"]
        if (not settings["is_symmetric"] or quantity != total or not 2 <= quantity <= 1024
                or not math.isclose(settings["total_angle_radians"], math.pi, abs_tol=1e-9)):
            raise ValueError("Symmetric circular index rule is bounded to positive180-degree patterns")
        return quantity//2
    if settings["kind"] != "SketchRectangularPattern":
        raise ValueError("Unsupported symmetric pattern index family")
    first, second = settings["quantity_one"], settings["quantity_two"]
    if (not (settings["symmetric_one"] or settings["symmetric_two"])
            or not 2 <= first <= 1024 or not 2 <= second <= 1024
            or first*second != total or not 2 <= total <= 1024
            or settings["distance_type"] != "Spacing" or settings.get("direction_selections")
            or not same(settings["direction_one"],[1,0,0]) or not same(settings["direction_two"],[0,1,0])
            or not all(math.isfinite(settings["distance_"+side+"_cm"]) and settings["distance_"+side+"_cm"] > 0 for side in ("one","two"))):
        raise ValueError("Symmetric rectangular index rule requires positive default-axis Spacing and nontrivial axis counts")
    column = (first-1)//2 if settings["symmetric_one"] else 0
    row = (second-1)//2 if settings["symmetric_two"] else 0
    return column+first*row


def observed_symmetric_suppression(indices, settings, total):
    """Convert native lattice indices to API ordinals, rejecting the seed."""
    seed = symmetric_seed_lattice_index(settings,total)
    if (len(indices) != len(set(indices))
            or any(type(index) is not int or not 0 <= index < total or index == seed for index in indices)):
        raise ValueError("Symmetric suppression native index is duplicated, outside its lattice, or names the unsuppressible seed")
    return [index+1 if index < seed else index for index in indices]


def decode_sketch_symmetric_indices(data, records, features):
    """Reuse coverage framing and add the observed rule only to symmetric results."""
    result = decode_sketch_pattern_coverage(data,records,features,
        symmetric_suppression_mapper=observed_symmetric_suppression)
    result["scope"] = "Existing Point/one-direction coverage plus observed symmetric lattice-index rule for single Circle seeds; common16-dependency bound retained"
    for pattern in result["patterns"]:
        if "native_suppressed_indices" not in pattern:
            continue
        seed = symmetric_seed_lattice_index(pattern,pattern["instance_count"])
        pattern["derived_seed_lattice_index"] = seed
        pattern["native_to_api_suppression_mapping"] = [
            {"native_lattice_index":native,"api_instance_ordinal":ordinal,"api_mask_index":ordinal-1}
            for native,ordinal in zip(pattern["native_suppressed_indices"],pattern["suppressed_instance_ordinals"])]
        for group in pattern["instance_groups"]:
            ordinal = group["instance_ordinal"]
            group["derived_native_lattice_index"] = seed if ordinal == 0 else ordinal-1 if ordinal <= seed else ordinal
        pattern["suppression_status"] = "Native lattice indices normalized around the derived symmetric seed position; raw indices and normalized API ordinals retained"
        pattern["suppression_mapping_status"] = "Control-derived index rule checked against quantity/axis and discriminating boundary holdouts; no coordinate-based identity assignment"
        if pattern["kind"] == "SketchRectangularPattern":
            pattern["derived_seed_lattice_row"] = seed//pattern["quantity_one"]
            pattern["derived_seed_lattice_column"] = seed%pattern["quantity_one"]
        pattern["captured_coverage_variants"] = ["ObservedSymmetricLatticeSuppression"]
    return result

"""Rectangle text controls established by eight API captures plus plain baseline.

The shared text reader retains source, rectangle and parameter validation. This
module only interprets the experimentally varied source-control fields.
"""

import math
import struct

from decode_sketch_texts import OPAQUE_PREFIX, OPAQUE_LAYOUT, decode_sketch_texts


ALIGNMENT = {1: 0, 3: 1, 2: 2}


def decode_rectangle_text_controls(prefix, flags, tail, *, allowed_layouts=(OPAQUE_LAYOUT,)):
    """Shared-reader callback; validates invariant bytes before returning controls."""
    if len(prefix) != 25 or prefix[:1]+prefix[9:] != OPAQUE_PREFIX[:1]+OPAQUE_PREFIX[9:]:
        raise ValueError("Unobserved rectangle text prefix controls")
    multiplier = struct.unpack_from("<d", prefix, 1)[0]
    spacing = (multiplier-1.)*100.
    if not math.isfinite(multiplier) or not math.isfinite(spacing) or multiplier < 1.:
        raise ValueError("Unverified negative or non-finite rectangle text spacing")
    if len(flags) != 7 or flags[6] != 0 or flags[4] not in (0, 1) or flags[5] not in (0, 1):
        raise ValueError("Unobserved rectangle text formatting flags")
    horizontal = struct.unpack_from("<I", flags, 0)[0]
    if len(tail) != 183 or tail[9:172] not in allowed_layouts or tail[4] not in (0, 1):
        raise ValueError("Unobserved rectangle text layout controls")
    vertical, weight = struct.unpack_from("<I", tail, 0)[0], struct.unpack_from("<I", tail, 5)[0]
    if horizontal not in ALIGNMENT or vertical not in ALIGNMENT or weight not in (400, 700):
        raise ValueError("Unobserved rectangle text alignment or font weight")
    return {
        "text_properties": {
            "text_style": (1 if weight == 700 else 0) | (2 if flags[5] else 0),
            "text_style_status": "Observed native weight and italic controls agree with API styles0/1/2/3; requested underline4 normalized to actual0 without a native contrast",
            "bold": weight == 700, "italic": bool(flags[5]), "native_font_weight": weight,
            "underline": None, "is_horizontal_flip": bool(flags[4]), "is_vertical_flip": bool(tail[4]),
        },
        "definition_properties": {
            "horizontal_alignment": ALIGNMENT[horizontal], "vertical_alignment": ALIGNMENT[vertical],
            "character_spacing_percent": spacing, "native_character_spacing_multiplier": multiplier,
            "native_horizontal_alignment": horizontal, "native_vertical_alignment": vertical,
            "spacing_status": "Percentage derived from native multiplier: captured1->0%,1.25->25%; negative spacing unverified",
        },
    }


def decode_sketch_text_controls(data, records, features):
    """Decode observed rectangle text with expanded controls and common ownership."""
    result = decode_sketch_texts(data, records, features, controls_decoder=decode_rectangle_text_controls)
    result["scope"] = "Rectangle SketchText source/ownership plus observed flips, styles0..3, alignment and derived nonnegative spacing; underline encoding unverified"
    for text in result["texts"]:
        text["definition"]["status"] = "Explicit owned rectangle and experimentally varied alignment/spacing controls; glyph rendering not decoded"
    return result

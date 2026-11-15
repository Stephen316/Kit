"""Generate and compare default SOLIDWORKS sketch styling fields for pinned P01."""

from collections import Counter
from enum import IntEnum
from struct import Struct
import json

from RectangleFields import (
    KApplicationBuild,
    MEMBER_MODE,
    MEMBER_TALLY,
    REVISION,
    exact_field,
    member_prefix,
    pinned_captures,
    read_profile,
    require,
    sha256,
)


class Weight(IntEnum):
    NONE = -1
    THIN = 0
    NORMAL = 1


VISUAL_PREFIX = Struct("<hHBIh")
STANDARD_WIDTH = Struct("<hf")
COLOR_STATUS_TYPE = Struct("<3H")
NO_LAYER = -1
ALL_BY_LAYER = 0x1F
INITIAL_VISUAL_STATE = 3
NO_COLOR = 0xFFFFFFFF
NO_STYLE = -1
NO_CUSTOM_WIDTH = -1.0


def standard_width(weight):
    require(isinstance(weight, Weight), "expected a declared standard line weight")
    return STANDARD_WIDTH.pack(weight, NO_CUSTOM_WIDTH)


def default_visual():
    return VISUAL_PREFIX.pack(
        NO_LAYER, ALL_BY_LAYER, INITIAL_VISUAL_STATE, NO_COLOR, NO_STYLE
    ) + standard_width(Weight.NONE)


def initial_display_state():
    # the sg2DEnt constructors initialize the three named store fields before solving
    return COLOR_STATUS_TYPE.pack(5, 1, 1)


def compare_style(blob, span, role, weight):
    prefix = member_prefix(blob, span)
    visual_start, visual_end = prefix["visual"]
    visual_span = exact_field(
        blob, visual_start, default_visual(), visual_end, "default visual"
    )
    state_start = prefix["tally"] + MEMBER_TALLY.size + MEMBER_MODE.size
    width_start = state_start + COLOR_STATUS_TYPE.size
    width_span = exact_field(
        blob,
        width_start,
        standard_width(weight),
        prefix["external_pointer"],
        "standard width",
    )
    state_values = COLOR_STATUS_TYPE.unpack_from(blob, state_start)
    require(
        width_span[1] == prefix["external_pointer"],
        "width extension does not reach its pointer",
    )
    state_span = None
    if role == "structural_header":
        state_span = exact_field(
            blob,
            state_start,
            initial_display_state(),
            width_start,
            "initial structural member display state",
        )
    return {
        "role": role,
        "native_id": prefix["native_id"],
        "visual": visual_span,
        "standard_width": width_span,
        "weight": weight.name.lower(),
        "display_state": {
            "color": state_values[0],
            "constraint_status": state_values[1],
            "line_type": state_values[2],
            "constructor_match": state_span,
        },
    }


def style_rows(blob, profile):
    rows = []
    for point in profile.Members.Points:
        prefix = member_prefix(blob, point)
        role = "origin_proxy" if prefix["mode"] == 1 else "corner"
        rows.append(compare_style(blob, point, role, Weight.THIN))
    for span, line in zip(
        profile.Members.Lines, profile.Geometry["lines"], strict=True
    ):
        if line["native_id"] < 0:
            rows.append(compare_style(blob, span, "structural_header", Weight.THIN))
        else:
            rows.append(compare_style(blob, span, "perimeter", Weight.NORMAL))
    require(
        Counter(row["role"] for row in rows)
        == {"corner": 4, "origin_proxy": 1, "structural_header": 1, "perimeter": 4},
        "unexpected P01 styling roster",
    )
    return rows


def report():
    measurements, captures = pinned_captures()
    cases = []
    for name, digest, raw, _ in captures:
        resolved, profile = read_profile(raw, name)
        cases.append(
            {
                "archive": name,
                "source_sha256": digest,
                "resolved_sha256": sha256(resolved),
                "members": style_rows(resolved, profile),
            }
        )
    return {
        "scope": "p01-inline-sketch-default-style",
        "capture_revision": REVISION,
        "application_build": KApplicationBuild,
        "measurements": measurements,
        "native_candidate_emitted": False,
        "cases": cases,
    }


if __name__ == "__main__":
    print(json.dumps(report(), sort_keys=True, separators=(",", ":")))

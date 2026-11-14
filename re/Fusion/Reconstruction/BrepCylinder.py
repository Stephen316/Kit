import argparse
import dataclasses
import hashlib
import json
import math
from pathlib import Path


@dataclasses.dataclass(frozen=True)
class Reference:
    index: int


@dataclasses.dataclass(frozen=True)
class CountedText:
    value: str


@dataclasses.dataclass(frozen=True)
class Keyword:
    value: str


@dataclasses.dataclass(frozen=True)
class Field:
    name: str
    value: object
    derivation: str


@dataclasses.dataclass(frozen=True)
class Record:
    name: str
    fields: tuple[Field, ...]


@dataclasses.dataclass(frozen=True)
class Cylinder:
    radius_mm: float
    height_mm: float
    base_mm: tuple[float, float, float]

    def __post_init__(self):
        if any(not math.isfinite(value) for value in (self.radius_mm, self.height_mm, *self.base_mm)):
            raise ValueError("Cylinder dimensions must be finite")
        if self.radius_mm <= 0 or self.height_mm <= 0:
            raise ValueError("Cylinder dimensions must be positive")


def token(value):
    if isinstance(value, Reference):
        return f"${value.index}"
    if isinstance(value, CountedText):
        return f"@{len(value.value.encode('utf-8'))} {value.value}"
    if isinstance(value, Keyword):
        return value.value
    if isinstance(value, tuple):
        return " ".join(token(item) for item in value)
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float) and math.isfinite(value):
        return format(value, ".17g")
    raise ValueError(f"Unsupported SMT token: {value!r}")


def field(name, value, derivation):
    return Field(name, value, derivation)


def link(name, index):
    return field(name, Reference(index), "Index of the named record in this newly allocated record table")


def common():
    return (
        field("attribute", Reference(-1), "No attributes are attached"),
        field("history_key", -1, "No history partition is emitted"),
        field("reserved_reference", Reference(-1), "Null profile observed in the native control; non-null meaning unresolved"),
    )


def build_records(model):
    x, y, z = model.base_mm
    r = model.radius_mm
    base = (x, y, z)
    top = (x, y, z + model.height_mm)
    axis = (0.0, 0.0, 1.0)
    major = (r, 0.0, 0.0)
    unbounded = lambda name: field(name, Keyword("I"), "Infinite parameter bound")
    sense = lambda value: field("sense", Keyword(value), "Orientation required for outward-facing cylinder shell")
    make = lambda name, *fields: Record(name, (*common(), *fields))
    records = [
        Record("asmheader", (
            field("attribute", Reference(-1), "No attributes are attached"),
            field("history_key", -1, "No history partition is emitted"),
            field("asm_version", CountedText("232.5.0.65535"), "Declared ASM schema version supported by native control"),
        )),
        make("body", link("first_lump", 2), link("wire", -1), link("transform", -1)),
        make("lump", link("next_lump", -1), link("first_shell", 3), link("owner_body", 1)),
        make("shell", link("next_shell", -1), link("subshell", -1), link("first_face", 4), link("wire", -1), link("owner_lump", 2)),
    ]
    for next_face, loop, surface, orientation in ((5, 7, 17, "forward"), (6, 9, 18, "forward"), (-1, 10, 19, "reversed")):
        records.append(make("face", link("next_face", next_face), link("first_loop", loop), link("owner_shell", 3), link("reserved_face_reference", -1), link("surface", surface), sense(orientation), field("sidedness", Keyword("single"), "One-sided manifold solid face")))
    for next_loop, coedge, face in ((8, 11, 4), (-1, 12, 4), (-1, 13, 5), (-1, 14, 6)):
        records.append(make("loop", link("next_loop", next_loop), link("first_coedge", coedge), link("owner_face", face)))
    for own, partner, edge, orientation, loop in ((11, 13, 15, "reversed", 7), (12, 14, 16, "forward", 8), (13, 11, 15, "forward", 9), (14, 12, 16, "reversed", 10)):
        records.append(make("coedge", link("next_coedge", own), link("previous_coedge", own), link("partner_coedge", partner), link("edge", edge), sense(orientation), link("owner_loop", loop), field("reserved_integer", 0, "Zero profile observed in the native control; other values unresolved"), link("pcurve", -1)))
    for vertex, coedge, curve in ((20, 11, 22), (21, 12, 23)):
        records.append(make("edge", link("start_vertex", vertex), field("start_parameter", -math.pi, "Start of full-circle parameter interval"), link("end_vertex", vertex), field("end_parameter", math.pi, "End of full-circle parameter interval"), link("owner_coedge", coedge), link("curve", curve), sense("forward"), field("convexity", CountedText("unknown"), "No precomputed convexity classification")))
    records.append(make("cone-surface", field("origin_mm", base, "Cylinder base center"), field("axis", axis, "Positive Z cylinder axis"), field("major_axis_mm", major, "Positive X radius vector"), field("ellipse_ratio", 1.0, "Circular cross section"), unbounded("ellipse_bound_start"), unbounded("ellipse_bound_end"), field("sine_angle", 0.0, "Zero cone half-angle yields a cylinder"), field("cosine_angle", 1.0, "Cosine of zero cone half-angle"), field("u_scale_mm", r, "Chosen canonical surface parameter length scale"), sense("forward"), unbounded("u_start"), unbounded("u_end"), unbounded("v_start"), unbounded("v_end")))
    for center in (top, base):
        records.append(make("plane-surface", field("origin_mm", center, "Cylinder cap center"), field("normal", axis, "Positive Z support-plane normal; face sense selects outward direction"), field("reference_axis", (1.0, 0.0, 0.0), "Independent unit X parameter reference, not donor radius vector"), field("v_sense", Keyword("forward_v"), "Canonical right-handed plane parameter frame"), unbounded("u_start"), unbounded("u_end"), unbounded("v_start"), unbounded("v_end")))
    for edge, point in ((15, 24), (16, 25)):
        records.append(make("vertex", link("owner_edge", edge), field("edge_index", 0, "Start-edge reference profile; native closed-circle control also has value 2 whose semantics remain unresolved"), link("point", point)))
    for center in (top, base):
        records.append(make("ellipse-curve", field("center_mm", center, "Cylinder cap center"), field("normal", axis, "Positive Z circle normal"), field("major_axis_mm", major, "Positive X radius vector"), field("ellipse_ratio", 1.0, "Circle major/minor ratio"), unbounded("parameter_start"), unbounded("parameter_end")))
    for center in (top, base):
        point = (center[0] + r * math.cos(-math.pi), center[1] + r * math.sin(-math.pi), center[2])
        records.append(make("point", field("position_mm", point, "Circle evaluated at the edge start parameter -pi")))
    return records


def smt_bytes(records):
    strings = ("Kit", "Independent SMT research", "Thu Nov 12 00:00:00 2026")
    lines = [
        "23200 0 2 2",
        " ".join(f"{len(value.encode('utf-8'))} {value}" for value in strings),
        "1 1e-6 1e-10",
        *(record.name + " " + " ".join(token(item.value) for item in record.fields) + " #" for record in records),
        "End-of-ASM-data",
    ]
    return ("\n".join(lines) + "\n").encode("utf-8")


def evidence(model, records, data):
    x, y, z = model.base_mm
    r = model.radius_mm
    h = model.height_mm
    return {
        "artifact_kind": "Independent research SMT solid; native acceptance pending",
        "source_dependencies": [],
        "input_model": dataclasses.asdict(model),
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
        "header": {
            "save_format": 23200,
            "stored_record_count": 0,
            "first_owned_record": 2,
            "flags": 2,
            "history_present": False,
            "revision": 1,
            "millimeters_per_unit": 1,
            "absolute_tolerance": 1e-6,
            "normal_tolerance": 1e-10,
            "authoring_timestamp": "Fixed research provenance string, not source timestamp",
        },
        "expected_native_observation": {
            "solid_body_count": 1,
            "faces": 3,
            "edges": 2,
            "vertices": 2,
            "volume_cm3": math.pi * (r / 10) ** 2 * (h / 10),
            "center_of_mass_cm": [x / 10, y / 10, (z + h / 2) / 10],
            "bounding_box_min_cm": [(x - r) / 10, (y - r) / 10, z / 10],
            "bounding_box_max_cm": [(x + r) / 10, (y + r) / 10, (z + h) / 10],
        },
        "record_count": len(records),
        "records": [{"index": index, **dataclasses.asdict(record)} for index, record in enumerate(records)],
        "limitations": [
            "Independent analytic cylinder only; no parametric features or history partition",
            "No Fusion Design/BRep Body-map identity relationship is emitted",
            "Reserved null references, coedge integer and vertex edge-index have only bounded observed profiles",
            "Native acceptance must be obtained separately and does not establish full F3D writer acceptance",
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--radius-mm", type=float, default=15.0)
    parser.add_argument("--height-mm", type=float, default=11.0)
    parser.add_argument("--base-mm", type=float, nargs=3, default=(20.0, -30.0, 5.0))
    args = parser.parse_args()
    model = Cylinder(args.radius_mm, args.height_mm, tuple(args.base_mm))
    records = build_records(model)
    data = smt_bytes(records)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(data)
    report = evidence(model, records, data)
    args.output.with_suffix(".derivation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in ("sha256", "bytes", "record_count", "expected_native_observation")}, indent=2))


if __name__ == "__main__":
    main()

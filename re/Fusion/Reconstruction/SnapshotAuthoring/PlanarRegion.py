import dataclasses
import math

from BrepCylinder import CountedText, Keyword, Record, Reference, field


@dataclasses.dataclass(frozen=True)
class CircleRegion:
    radius_mm: float
    center_mm: tuple[float, float, float]

    def __post_init__(self):
        if len(self.center_mm) != 3 or self.radius_mm <= 0:
            raise ValueError("Planar circle requires positive radius and three coordinates")
        if not all(math.isfinite(value) for value in (self.radius_mm, *self.center_mm)):
            raise ValueError("Planar circle geometry must be finite")


def common():
    return (
        field("attribute", Reference(-1), "Attribute head assigned after allocating all topology"),
        field("identity", -1, "Snapshot entities have no nonnegative ASM body key"),
        field("reserved_reference", Reference(-1), "Observed nullable entity profile"),
    )


def link(name, index):
    return field(name, Reference(index), "Index allocated in this complete new snapshot table")


def make(name, *fields):
    return Record(name, (*common(), *fields))


def region_records(region: CircleRegion, body_index, start, double_sided):
    lump, shell, face, loop, coedge, edge, vertex, ellipse, plane, point = range(start, start + 10)
    radius = region.radius_mm
    center = region.center_mm
    forward = field("sense", Keyword("forward"), "Positive circle traversal and plane normal")
    bound = lambda name: field(name, Keyword("I"), "Unbounded analytic carrier parameter")
    face_fields = (
        link("next_face", -1), link("first_loop", loop), link("owner_shell", shell),
        link("reserved_face_reference", -1), link("surface", plane), forward,
        field("sidedness", Keyword("double" if double_sided else "single"), "Explicit cached profile-body role"),
    )
    if double_sided:
        face_fields += (field("containment", False, "Observed double-sided region containment profile"),)
    result = [
        make("lump", link("next_lump", -1), link("first_shell", shell), link("owner_body", body_index)),
        make("shell", link("next_shell", -1), link("first_subshell", -1), link("first_face", face), link("wire", -1), link("owner_lump", lump)),
        make("face", *face_fields),
        make("loop", link("next_loop", -1), link("first_coedge", coedge), link("owner_face", face)),
        make("coedge", link("next_coedge", coedge), link("previous_coedge", coedge), link("partner", -1), link("edge", edge), forward, link("owner_loop", loop), field("reserved_integer", 0, "Observed coedge profile"), link("pcurve", -1)),
        make("edge", link("start_vertex", vertex), field("start_parameter", -math.pi, "Beginning of full-circle traversal"), link("end_vertex", vertex), field("end_parameter", math.pi, "End of full-circle traversal"), link("owner_coedge", coedge), link("curve", ellipse), forward, field("convexity", CountedText("unknown"), "No precomputed edge convexity")),
        make("vertex", link("owner_edge", edge), field("edge_index", 0, "Observed start-reference profile for the closed circle"), link("point", point)),
        make("ellipse-curve", field("center_mm", center, "Semantic sketch circle center"), field("normal", (0.0, 0.0, 1.0), "Positive Z sketch plane normal"), field("major_axis_mm", (radius, 0.0, 0.0), "Semantic circle radius vector"), field("ellipse_ratio", 1.0, "Circular carrier"), bound("parameter_start"), bound("parameter_end")),
        make("plane-surface", field("origin_mm", center, "Semantic sketch plane origin"), field("normal", (0.0, 0.0, 1.0), "Positive Z sketch plane normal"), field("reference_axis", (1.0, 0.0, 0.0), "Dimensionless unit X parameter frame"), field("v_sense", Keyword("forward_v"), "Right-handed plane parameter frame"), bound("u_start"), bound("u_end"), bound("v_start"), bound("v_end")),
        make("point", field("position_mm", (center[0] + radius * math.cos(-math.pi), center[1] + radius * math.sin(-math.pi), center[2]), "Circle evaluated at its starting edge parameter")),
    ]
    root = make("body", link("first_lump", lump), link("wire", -1), link("transform", -1))
    return root, result

from hashlib import sha256
from itertools import product
from math import dist
from struct import calcsize

from CmgrBossMass import BossMassFields, EncodeBossMass, ReadBossMass
from CmgrMass import KGeometryLayout
from DefinitionTail import ReadPartDefinitionTail
from convert.adapters.solidworks.Container.Archive import ArchiveError
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor, FieldCursor
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Resolved.RectanglePart import RectanglePart, ReadRectPart

GEOMETRY_TOLERANCES = (1e-15,) * 3 + (1e-19, 1e-17, 1e-16) + (1e-20,) * 6


# The basis and scale come from the profile's resolved principal datum.
def to_world(point, u_axis, v_axis, shift_scale):
    x, y = point
    tx, ty, tz, scale = shift_scale
    return tuple(
        scale * (u * x + v * y) + shift
        for u, v, shift in zip(u_axis, v_axis, (tx, ty, tz), strict=True)
    )


# Establish cuboid bounds from typed edges and signed blind extent before using mass.
def boss_bounds(part: RectanglePart, measurement):
    boss = part.Boss
    if boss is None:
        raise ArchiveError("CMgr mass evidence needs a typed rectangular boss")
    (feature,) = [row for row in measurement["feature_tree"] if row["type"] == "Extrusion"]
    operation = feature["operation"]
    saved_end = boss["end_specification"]
    sign = -1 if saved_end["direction"] else 1
    depth = boss["depth_display"]["dimension"]["metres"]
    expected_sign = -1 if operation["reverse_direction"] else 1
    RequireArch(
        (
            boss["name"],
            sign,
            depth,
            operation["end_condition"],
            operation["both_directions"],
        ),
        (feature["name"], expected_sign, operation["depth_m"], 0, False),
        "CMgr mass owner and independently measured blind extent",
    )
    (sketch,) = [
        row for row in measurement["sketches"] if row["name"] == part.Profile.NameValue
    ]
    RequireArch(sketch["support_name"], part.Datum.NameValue, "CMgr mass profile support")
    geometry = part.Profile.Geometry
    u_axis, v_axis, normal = part.Directions
    edges = [line for line in geometry["lines"] if line["native_id"] >= 0]
    measured = {tuple(line["id"]): line for line in sketch["entities"]}
    RequireArch(
        (len(edges), len(measured), len(sketch["entities"])),
        (4, 4, 4),
        "CMgr mass profile perimeter",
    )
    corners = set()
    for edge in edges:
        native_id = edge["native_id"]
        line = measured.pop((native_id, native_id))
        RequireArch(
            (line["type"], line["construction"]), (0, False), "CMgr mass perimeter lines"
        )
        ends = tuple(
            to_world(
                geometry["points_metres"][index], u_axis, v_axis, part.Reference.ShiftScale
            )
            for index in edge["point_indices"]
        )
        for point, field in zip(ends, ("start_world_mm", "end_world_mm"), strict=True):
            expected_m = tuple(value * 1e-3 for value in line[field])
            RequireArch(
                dist(point, expected_m) <= 1e-12, True, "CMgr mass perimeter endpoint"
            )
        corners.update(ends)
    RequireArch(len(corners), 4, "CMgr mass unique rectangle corners")
    delta = tuple(sign * depth * value for value in normal)
    vertices = corners | {
        tuple(value + step for value, step in zip(point, delta, strict=True))
        for point in corners
    }
    RequireArch(len(vertices), 8, "CMgr mass unique cuboid corners")
    bounds = tuple((min(axis), max(axis)) for axis in zip(*vertices, strict=True))
    RequireArch(vertices, set(product(*bounds)), "CMgr mass axis aligned cuboid")
    lowest, highest = zip(*bounds, strict=True)
    return lowest, highest


# The exact wrappers and the physical kernel outputs have different comparison rules.
def verify_boss_mass(
    cursor: ArchiveCursor,
    archive: SldprtArchive,
    generation: int,
    measurement,
    asset: str,
) -> str:
    part = ReadRectPart(
        archive.require("Contents/Config-0"),
        archive.require("Contents/Config-0-ResolvedFeatures"),
        generation,
    )
    lowest, highest = boss_bounds(part, measurement)
    definition = archive.require("Contents/Definition")
    density = ReadPartDefinitionTail(
        definition, len(definition) - calcsize("<id"), generation
    )
    body_count = measurement["body_count"]
    start = cursor.Offset
    saved = ReadBossMass(cursor, generation, body_count)
    RequireArch((start, cursor.Offset), (1234, 1488), "CMgr boss mass extent")
    geometry_width = calcsize(KGeometryLayout)
    saved_wrapper = cursor.BlobValue[start + geometry_width : cursor.Offset]
    generated = EncodeBossMass(generation, body_count, lowest, highest, density)
    RequireArch(len(generated), cursor.Offset - start, "CMgr encoded boss mass width")
    RequireArch(
        generated[geometry_width:] == saved_wrapper,
        True,
        "CMgr boss mass options and coordinates",
    )
    generated_cursor = FieldCursor(generated, 0)
    readback = ReadBossMass(generated_cursor, generation, body_count)
    RequireArch(generated_cursor.Offset, len(generated), "CMgr generated mass return")
    deltas = tuple(
        abs(new - native)
        for new, native in zip(BossMassFields(readback), BossMassFields(saved), strict=True)
    )
    RequireArch(
        all(
            delta <= limit
            for delta, limit in zip(deltas, GEOMETRY_TOLERANCES, strict=True)
        ),
        True,
        f"CMgr boss mass geometry in {asset}: {deltas}",
    )
    RequireArch(cursor.ReadInts("<I"), (631152000,), "CMgr saved configuration time")
    cursor.ReadNull()
    RequireArch(
        cursor.ReadInts("<HiB"),
        (0, body_count, 0),
        "CMgr base list solid count and default accuracy",
    )
    RequireArch(cursor.Offset, 1501, "CMgr default accuracy return")
    return sha256(saved_wrapper).hexdigest()

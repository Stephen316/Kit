# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

# historical geometry fields stay isolated so dataclass reflection expectations remain reviewable
KCompatFieldsGeometry = (
    (
        "interchange.geometry.ArcEllipseGeometry",
        (
            "center",
            "major_axis",
            "major_radius",
            "minor_radius",
            "start_angle",
            "end_angle",
        ),
    ),
    (
        "interchange.geometry.ArcGeometry",
        ("center", "radius", "start_angle", "end_angle"),
    ),
    (
        "interchange.geometry.ArcHyperbolaGeometry",
        (
            "center",
            "major_axis",
            "major_radius",
            "minor_radius",
            "start_angle",
            "end_angle",
        ),
    ),
    (
        "interchange.geometry.ArcParabolaGeometry",
        ("center", "axis", "focal_length", "start_angle", "end_angle"),
    ),
    ("interchange.geometry.CircleGeometry", ("center", "radius")),
    ("interchange.geometry.ConstraintReference", ("entity_id", "point")),
    (
        "interchange.geometry.EllipseGeometry",
        ("center", "major_axis", "major_radius", "minor_radius"),
    ),
    (
        "interchange.geometry.HyperbolaGeometry",
        ("center", "major_axis", "major_radius", "minor_radius"),
    ),
    ("interchange.geometry.LineGeometry", ("start", "end")),
    ("interchange.geometry.NativeGeometry", ("format_id", "entity_type", "data")),
    ("interchange.geometry.ParabolaGeometry", ("center", "axis", "focal_length")),
    ("interchange.geometry.PointGeometry", ("point",)),
    (
        "interchange.geometry.Selection",
        ("id", "name", "path", "query", "point", "provenance", "attributes"),
    ),
    (
        "interchange.geometry.SelectionPathElement",
        ("entity_kind", "entity_id", "subelement"),
    ),
    (
        "interchange.geometry.Sketch",
        (
            "id",
            "name",
            "support_plane_id",
            "entities",
            "constraints",
            "parameter_ids",
            "closed_profile_entity_ids",
            "suppressed",
            "provenance",
            "attributes",
        ),
    ),
    (
        "interchange.geometry.SketchConstraint",
        (
            "id",
            "kind",
            "references",
            "parameter_id",
            "driving",
            "suppressed",
            "provenance",
            "attributes",
        ),
    ),
    (
        "interchange.geometry.SketchEntity",
        ("id", "kind", "geometry", "construction", "fixed", "provenance", "attributes"),
    ),
    (
        "interchange.geometry.SplineGeometry",
        ("control_points", "degree", "knots", "multiplicities", "weights", "periodic"),
    ),
    (
        "interchange.geometry.SupportPlane",
        (
            "id",
            "name",
            "transform",
            "support_selection_id",
            "offset_parameter_id",
            "provenance",
            "attributes",
        ),
    ),
)

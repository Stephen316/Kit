from convert.formats.Fusion.GraphicsCodec.Schema.FieldRule import FieldRule

KVersionRules: dict[tuple[str, int], tuple[FieldRule, ...]] = {
    ("BillBoardAttribute", 1): (
        FieldRule("Style", "i32"),
        FieldRule("Anchor", "f32", 3),
        FieldRule("Axis", "f32", 3),
        FieldRule("Compensation", "f32", 3),
    ),
}

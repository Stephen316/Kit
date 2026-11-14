def require_resolved_lengths(findings):
    expected_dimensions = {
        "P01": {"width_mm@RectangleSketch", "height_mm@RectangleSketch"},
        "P03": {"width_mm@RectangleSketch", "height_mm@RectangleSketch", "depth_mm@BlindBoss"},
        "P04": {"depth_mm@BlindBoss", "cut_depth_mm@BlindCut"},
    }
    inch_cases = [
        entry for entry in findings if entry["asset"]["path"].endswith("-units-inch.SLDPRT")
    ]
    cases = {entry["recipe_id"]: entry for entry in inch_cases}
    if len(inch_cases) != len(cases) or set(cases) != set(expected_dimensions):
        raise ValueError("inch-length check requires the P01, P03 and P04 inch captures")
    for recipe_id, names in expected_dimensions.items():
        entry = cases[recipe_id]
        matched = {row["field"] for row in entry["comparisons"] if row["status"] == "matched"}
        expected = {"neutral.source_display_unit"} | {
            f"{stage}.dimension.{name}" for stage in ("native", "neutral") for name in names
        }
        if recipe_id in {"P03", "P04"}:
            expected.update(f"{stage}.operation.BlindBoss.depth_mm" for stage in ("native", "neutral"))
        if recipe_id == "P04":
            expected.update(f"{stage}.operation.BlindCut.depth_mm" for stage in ("native", "neutral"))
        if missing := expected - matched:
            raise ValueError(f"resolved inch lengths differ for {entry['asset']['path']}: {sorted(missing)}")
    print("Verified seven resolved-feature dimensions and three operation depths across the inch captures")
